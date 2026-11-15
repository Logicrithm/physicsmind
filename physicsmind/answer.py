"""Decides who answers a question and writes the reply.

1. The question reader checks whether the solver can answer it with certainty.
2. Solvable: the solver answers, with every step, the quantities it read and its assumptions.
3. Unclear: no number is given. The reply says exactly what is missing, and the AI is not called.
4. Anything else goes to the AI tutor, labelled as unchecked, unless this visit's AI questions are used up.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re

from .projectile import solve_projectile
from .reader import HEIGHT, NOT_MINE, RANGE, SOLVABLE, T_FLIGHT, T_TOP, UNCLEAR, Reading, _show, read_question
from .tutor import LIMIT_REACHED, NOT_CONFIGURED, ask_tutor

SOLVER, CLARIFICATION, AI_TUTOR, AI_UNAVAILABLE = "solver", "clarification", "ai_tutor", "ai_unavailable"
AI_LIMIT = "ai_limit"  # this visitor has used their AI questions for the visit; the AI was not called
TOO_LONG = "too_long"  # refused before anything ran, so one pasted essay can't use up the shared AI allowance

MAX_QUESTION_CHARS = 1500  # a long textbook question is about 600 characters
TOO_LONG_TEXT = (f"That message is too long for me (the limit is {MAX_QUESTION_CHARS} characters). Please send just the "
                 "physics question, and split a long problem into its parts.")

SOLVER_STILL_WORKS = ("Checked projectile questions (maximum height, time to the top, time of flight, range) still work, "
                      "because they don't need the AI.")
UNAVAILABLE_TEXT = {
    NOT_CONFIGURED: ("I'm ready to help! The AI tutor isn't connected yet, so I can't answer general physics questions "
                     "here. " + SOLVER_STILL_WORKS + "\n\nTo connect it on your own computer, add a free Groq or OpenRouter "
                     "API key to the `.env` file. See README.md."),
    LIMIT_REACHED: ("The free AI tutor has used up its answers for now. Free AI plans allow only a limited number of "
                    "answers a day, shared by everyone using PhysicsMind. " + SOLVER_STILL_WORKS +
                    " Please try your question again later or tomorrow."),
}
FAILED_TEXT = ("The AI tutor couldn't be reached just now, so I can't answer this one. " + SOLVER_STILL_WORKS +
               " Please try again in a minute.")
AI_LIMIT_TEXT = ("You've used the AI-tutor questions for this visit; each visit gets a few so the free daily allowance "
                 "lasts for everyone testing PhysicsMind. " + SOLVER_STILL_WORKS)


@dataclass
class Answer:
    text: str
    source: str          # shown under the answer
    response_type: str   # saved with feedback, so a wrong answer can be traced to the part that gave it
    verification: str
    used_ai: bool = False  # the AI tutor was asked (it counts towards the visit's allowance)


def make_answer(question: str, tutor=ask_tutor, ai_allowed: bool = True) -> Answer:
    # Checked here as well as in the chat box, because a modified browser can skip the chat box's own limit.
    if len(question) > MAX_QUESTION_CHARS:
        return Answer(TOO_LONG_TEXT, "PhysicsMind", TOO_LONG, "not answered: message too long")
    reading = read_question(question)
    if reading.status == SOLVABLE:
        solution = solve_projectile(reading)
        if solution.ok:
            return Answer(explain(reading, solution), "PhysicsMind solver (SymPy)", SOLVER,
                          "checked: SymPy result matches the direct formula")
        return Answer(f"I understood the question but couldn't confirm the answer, so I won't give a number. {solution.problem}",
                      "PhysicsMind solver", CLARIFICATION, "no number given: calculation could not be checked")
    if reading.status == UNCLEAR:
        return Answer(clarify(reading), "PhysicsMind question check", CLARIFICATION, "no number given: question unclear")

    note = ""
    if reading.on_topic and reading.status == NOT_MINE:
        note = (f"*The checked solver doesn't answer this one because {reading.reasons[0]}. "
                f"The AI tutor answers instead, and its numbers are not checked.*\n\n")
    if not ai_allowed:
        return Answer(note + AI_LIMIT_TEXT, "PhysicsMind", AI_LIMIT, "not answered: visit's AI questions used")
    answer, model, error = tutor(question)
    if error:
        return Answer(note + UNAVAILABLE_TEXT.get(error, FAILED_TEXT), model or "Not connected", AI_UNAVAILABLE,
                      "not answered: AI tutor unavailable", used_ai=error != NOT_CONFIGURED)
    return Answer(note + streamlit_math(answer), model or "unknown", AI_TUTOR, "LLM response; not independently verified",
                  used_ai=True)


def streamlit_math(text: str) -> str:
    r"""Many models write maths as \( ... \) and \[ ... \]. Streamlit only renders $ ... $ and $$ ... $$, so without
    this a student sees "J C(^{-1})" instead of the formula (found in the running app on 15 Nov 2026).

    Every display formula becomes a real maths block: "$$" alone on a line, the formula on one line, "$$" alone on
    a line. Streamlit starts a block only at a line holding nothing but "$$": "$$v_x = ..." followed by more lines
    lost its first line and never closed, so the rest of the answer showed as raw symbols (testers' feedback,
    15 Nov 2026), and "$$...$$" on one line is drawn as inline maths, where \tag and aligned equations fail.
    The block keeps the indent of its line, so a formula inside a numbered step stays inside that step.
    """
    def block(match: re.Match) -> str:
        latex = _one_line(match.group(1) if match.group(1) is not None else match.group(2))
        line_start = text.rfind("\n", 0, match.start()) + 1
        indent = re.match(r"[ \t]*", text[line_start:]).group()
        return f"\n\n{indent}$$\n{indent}{latex}\n{indent}$$\n\n"

    converted = DISPLAY_MATH.sub(block, text)
    converted = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", converted).strip("\n")  # no runs of empty lines
    return re.sub(r"\\\((.+?)\\\)", lambda m: f"${_one_line(m.group(1))}$", converted, flags=re.S)


# \[ ... \] (but not the "\\[2pt]" line break inside aligned maths) or the model's own $$ ... $$.
DISPLAY_MATH = re.compile(r"(?<!\\)\\\[(.+?)\\\]|\$\$(.+?)\$\$", re.S)


def _one_line(latex: str) -> str:
    """A formula on one line. A LaTeX comment (% to the end of the line) is dropped first, or joining would hide the rest."""
    lines = (re.sub(r"(?<!\\)%.*", "", line).strip() for line in latex.splitlines())
    return " ".join(line for line in lines if line)


def clarify(reading: Reading) -> str:
    lines = ["I want to get this right, so I haven't calculated anything yet. I need you to clear this up:", ""]
    lines += [f"- {reason}" for reason in reading.reasons]
    if reading.understood:
        lines += ["", "**What I understood so far**", ""] + [f"- {item}" for item in reading.understood]
    lines += ["", "Send the whole question again with that detail and I'll solve it step by step."]
    return "\n".join(lines)


def explain(reading: Reading, solution) -> str:
    asks = reading.asks or [HEIGHT]
    several = len(asks) > 1
    g, upward, h0 = reading.g, solution.upward_speed, reading.launch_height
    G, UY = _show(g), _show(upward)
    lines = ["**What I understood**", ""] + [f"- {item}" for item in reading.understood]
    lines += [f"- {note}" for note in reading.notes]
    lines += ["", "**Method**", ""]
    if reading.horizontal_launch:
        lines += ["Thrown horizontally, it starts with no upward speed: gravity pulls it down from the moment it leaves, "
                  "while its sideways speed stays the same.", "",
                  rf"$$u_x = u = {_show(solution.sideways_speed or reading.speed.value)}\ \text{{m/s}}, \qquad u_y = 0$$", ""]
    elif asks == [HEIGHT]:
        lines += ["At the highest point the object stops rising, so its vertical velocity there is zero. "
                  "Only the upward part of the launch speed lifts it; any sideways part doesn't change the height.", ""]
    else:
        lines += ["Gravity only changes the up-and-down motion: the upward speed drops by g every second, while the "
                  "sideways speed stays the same. So the two motions are worked out separately.", ""]
    if not reading.horizontal_launch and reading.vertical_speed is None and reading.speed is not None and reading.angle is not None:
        u, degrees = _show(reading.speed.value), _show(math.degrees(reading.angle))
        trig = r"\sin" if reading.angle_from == "horizontal" else r"\cos"
        lines += [f"Upward part of the launch speed (angle measured from the {reading.angle_from}):", "",
                  rf"$$u_y = u{trig}\theta = {u} \times {trig} {degrees}^\circ = {UY}\ \text{{m/s}}$$", ""]
        if RANGE in asks:
            side = r"\cos" if reading.angle_from == "horizontal" else r"\sin"
            lines += ["Sideways part:", "",
                      rf"$$u_x = u{side}\theta = {u} \times {side} {degrees}^\circ = {_show(solution.sideways_speed)}\ \text{{m/s}}$$", ""]
    elif reading.vertical_speed is None and reading.speed is None:
        t = _show(reading.time_to_top.value)
        lines += ["It takes the given time for gravity to bring the upward speed to zero:", "",
                  rf"$$v = u_y - gt \;\Rightarrow\; u_y = gt = {G} \times {t} = {UY}\ \text{{m/s}}$$", ""]

    if HEIGHT in asks:
        rise = solution.rise
        if several:
            lines += ["**Maximum height**", "", "At the highest point its upward speed is zero.", ""]
        lines += [r"Using $v^2 = u^2 + 2as$ upward, with $v = 0$ at the top and $a = -g$:", "",
                  r"$$0 = u_y^2 - 2gh \;\Rightarrow\; h = \frac{u_y^2}{2g}$$", "",
                  rf"$$h = \frac{{({UY})^2}}{{2 \times {G}}} = {rise:.2f}\ \text{{m}}$$", ""]
        if solution.above_ground is not None:
            lines += [f"It starts {_show(h0)} m above the ground, so its highest point is "
                      f"{_show(h0)} + {rise:.2f} = {solution.above_ground:.2f} m above the ground.", ""]
    if T_TOP in asks:
        lines += ["**Time to reach the top**", "",
                  r"Its upward speed falls to zero at the top. Using $v = u + at$ with $v = 0$ and $a = -g$:", "",
                  rf"$$0 = u_y - gt \;\Rightarrow\; t = \frac{{u_y}}{{g}} = \frac{{{UY}}}{{{G}}} = {solution.time_to_top:.2f}\ \text{{s}}$$", ""]
    if T_FLIGHT in asks or RANGE in asks:
        T = solution.time_of_flight
        lines += ["**Time of flight**" if T_FLIGHT in asks else "**Time in the air (needed for the range)**", ""]
        if h0 > 0:
            lines += [rf"It lands on the ground, {_show(h0)} m below where it started, so its vertical displacement is "
                      r"$s = -h_0$. Using $s = ut + \tfrac{1}{2}at^2$ with $a = -g$:", "",
                      r"$$-h_0 = u_yT - \tfrac{1}{2}gT^2$$", "",
                      "This has two solutions; the negative one would be before the launch, so the positive one is used:", ""]
            if upward == 0:
                lines += [r"With $u_y = 0$ this is", "",
                          rf"$$T = \sqrt{{\frac{{2h_0}}{{g}}}} = \sqrt{{\frac{{2 \times {_show(h0)}}}{{{G}}}}} = {T:.2f}\ \text{{s}}$$", ""]
            else:
                lines += [rf"$$T = \frac{{u_y + \sqrt{{u_y^2 + 2gh_0}}}}{{g}} = \frac{{{UY} + \sqrt{{{UY}^2 + 2 \times {G} \times {_show(h0)}}}}}{{{G}}}"
                          rf" = {T:.2f}\ \text{{s}}$$", ""]
        else:
            lines += [r"It lands back at the height it started from, so its vertical displacement is zero. "
                      r"Using $s = ut + \tfrac{1}{2}at^2$ with $a = -g$:", "",
                      rf"$$0 = u_yT - \tfrac{{1}}{{2}}gT^2 \;\Rightarrow\; T = \frac{{2u_y}}{{g}} = \frac{{2 \times {UY}}}{{{G}}} = {T:.2f}\ \text{{s}}$$", "",
                      "(The other solution, T = 0, is the moment it is launched.)", ""]
    if RANGE in asks:
        where = " from the point directly below where it was launched" if h0 > 0 else ""
        lines += ["**Horizontal range**", "",
                  f"Nothing pushes it sideways, so it keeps its sideways speed for the whole flight. The distance along the ground{where}:", "",
                  rf"$$R = u_xT = {_show(solution.sideways_speed)} \times {_show(solution.time_of_flight)} = {solution.range:.2f}\ \text{{m}}$$", ""]

    if not several and HEIGHT in asks:
        if solution.above_ground is not None:
            lines += [f"**Answer: it rises {solution.rise:.2f} m above its launch point, reaching {solution.above_ground:.2f} m above the ground.**"]
        else:
            lines += [f"**Answer: {solution.rise:.2f} m** (above the launch point)"]
    else:
        lines += ["**Answer**", ""]
        if HEIGHT in asks:
            lines += [f"- Maximum height: **{solution.rise:.2f} m** above the launch point"
                      + (f", **{solution.above_ground:.2f} m** above the ground" if solution.above_ground is not None else "")]
        if T_TOP in asks:
            lines += [f"- Time to reach the top: **{solution.time_to_top:.2f} s**"]
        if T_FLIGHT in asks:
            lines += [f"- Time of flight: **{solution.time_of_flight:.2f} s**"]
        if RANGE in asks:
            lines += [f"- Horizontal range: **{solution.range:.2f} m**"]
    assumptions = list(reading.assumptions)
    assumptions.append("Air resistance is neglected, as the question says." if reading.air_resistance_neglected
                       else "Air resistance is neglected and g is constant, the standard assumptions for these formulas.")
    lines += ["", "**Assumptions**", ""] + [f"- {item}" for item in assumptions]
    lines += ["", f"*Checked: {'; '.join(_pairs(solution.checks))}.*"]
    return "\n".join(lines)


def _pairs(checks: list[str]) -> list[str]:
    """The checks come in pairs (SymPy, then the direct formula): "A and B; C and D"."""
    return [" and ".join(checks[i:i + 2]) for i in range(0, len(checks), 2)]


