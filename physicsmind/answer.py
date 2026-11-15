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

from .projectile import solve_max_height
from .reader import NOT_MINE, SOLVABLE, UNCLEAR, Reading, _show, read_question
from .tutor import LIMIT_REACHED, NOT_CONFIGURED, ask_tutor

SOLVER, CLARIFICATION, AI_TUTOR, AI_UNAVAILABLE = "solver", "clarification", "ai_tutor", "ai_unavailable"
AI_LIMIT = "ai_limit"  # this visitor has used their AI questions for the visit; the AI was not called
TOO_LONG = "too_long"  # refused before anything ran, so one pasted essay can't use up the shared AI allowance

MAX_QUESTION_CHARS = 1500  # a long textbook question is about 600 characters
TOO_LONG_TEXT = (f"That message is too long for me (the limit is {MAX_QUESTION_CHARS} characters). Please send just the "
                 "physics question, and split a long problem into its parts.")

SOLVER_STILL_WORKS = "Checked maximum-height questions still work, because they don't need the AI."
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
        solution = solve_max_height(reading)
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
    this a student sees "J C(^{-1})" instead of the formula (found in the running app on 15 Nov 2026)."""
    text = re.sub(r"\\\[(.+?)\\\]", lambda m: f"$${m.group(1).strip()}$$", text, flags=re.S)
    return re.sub(r"\\\((.+?)\\\)", lambda m: f"${m.group(1).strip()}$", text, flags=re.S)


def clarify(reading: Reading) -> str:
    lines = ["I want to get this right, so I haven't calculated anything yet. I need you to clear this up:", ""]
    lines += [f"- {reason}" for reason in reading.reasons]
    if reading.understood:
        lines += ["", "**What I understood so far**", ""] + [f"- {item}" for item in reading.understood]
    lines += ["", "Send the whole question again with that detail and I'll solve it step by step."]
    return "\n".join(lines)


def explain(reading: Reading, solution) -> str:
    g, upward, rise = reading.g, solution.upward_speed, solution.rise
    lines = ["**What I understood**", ""] + [f"- {item}" for item in reading.understood]
    lines += [f"- {note}" for note in reading.notes]
    lines += ["", "**Method**", "",
              "At the highest point the object stops rising, so its vertical velocity there is zero. "
              "Only the upward part of the launch speed lifts it; any sideways part doesn't change the height.", ""]
    if reading.vertical_speed is None and reading.speed is not None and reading.angle is not None:
        u, degrees = _show(reading.speed.value), _show(math.degrees(reading.angle))
        trig = r"\sin" if reading.angle_from == "horizontal" else r"\cos"
        lines += [f"Upward part of the launch speed (angle measured from the {reading.angle_from}):", "",
                  rf"$$u_y = u{trig}\theta = {u} \times {trig} {degrees}^\circ = {_show(upward)}\ \text{{m/s}}$$", ""]
    elif reading.vertical_speed is None and reading.speed is None:
        t = _show(reading.time_to_top.value)
        lines += ["It takes the given time for gravity to bring the upward speed to zero:", "",
                  rf"$$v = u_y - gt \;\Rightarrow\; u_y = gt = {_show(g)} \times {t} = {_show(upward)}\ \text{{m/s}}$$", ""]
    lines += [r"Using $v^2 = u^2 + 2as$ upward, with $v = 0$ at the top and $a = -g$:", "",
              r"$$0 = u_y^2 - 2gh \;\Rightarrow\; h = \frac{u_y^2}{2g}$$", "",
              rf"$$h = \frac{{({_show(upward)})^2}}{{2 \times {_show(g)}}} = {rise:.2f}\ \text{{m}}$$", ""]
    if solution.above_ground is not None:
        lines += [f"It starts {_show(reading.launch_height)} m above the ground, so its highest point is "
                  f"{_show(reading.launch_height)} + {rise:.2f} = {solution.above_ground:.2f} m above the ground.", "",
                  f"**Answer: it rises {rise:.2f} m above its launch point, reaching {solution.above_ground:.2f} m above the ground.**"]
    else:
        lines += [f"**Answer: {rise:.2f} m** (above the launch point)"]
    assumptions = list(reading.assumptions)
    assumptions.append("Air resistance is neglected, as the question says." if reading.air_resistance_neglected
                       else "Air resistance is neglected and g is constant, the standard assumptions for this formula.")
    lines += ["", "**Assumptions**", ""] + [f"- {item}" for item in assumptions]
    lines += ["", f"*Checked: {' and '.join(solution.checks)}.*"]
    return "\n".join(lines)
