"""AI maths is converted so Streamlit can draw it (testers saw raw symbols on 15 Nov 2026). Streamlit draws a maths
block only between lines holding nothing but "$$"; "$$...$$" on one line is drawn as inline maths, where \\tag and
aligned equations fail."""
from pathlib import Path
import re

from physicsmind.answer import make_answer, streamlit_math

# A real answer from the AI tutor (Groq, openai/gpt-oss-120b, 15 Nov 2026) that showed as raw symbols in the app.
REAL_ANSWER = (Path(__file__).parent / "data" / "ai_answer_multiline_maths.md").read_text(encoding="utf-8")


def blocks_are_well_formed(text: str) -> bool:
    """Every "$$" stands alone on its line, they come in pairs, and each block holds exactly one formula line."""
    lines = text.splitlines()
    fences = [i for i, line in enumerate(lines) if "$$" in line]
    if any(lines[i].strip() != "$$" for i in fences) or len(fences) % 2:
        return False
    return all(close - open_ == 2 for open_, close in zip(fences[::2], fences[1::2]))


def test_the_real_answer_that_showed_raw_symbols_now_has_proper_maths_blocks():
    converted = streamlit_math(REAL_ANSWER)
    assert blocks_are_well_formed(converted)
    assert r"\[" not in converted and r"\(" not in converted
    # The formula that broke the page: two lines in the AI's answer, now one line inside its numbered step.
    assert "   $$\n   v_{0x}=v_0\\cos\\theta,\\qquad v_{0y}=v_0\\sin\\theta\n   $$" in converted
    assert converted.count("$$") == REAL_ANSWER.count(r"\[") * 2  # no formula lost or merged


def test_a_multi_line_formula_inside_a_numbered_step_stays_in_the_step():
    text = "1. **Components**\n\n   \\[\n   a = 1,\n   b = 2\n   \\]\n\n2. Next"
    assert streamlit_math(text) == "1. **Components**\n\n   $$\n   a = 1, b = 2\n   $$\n\n2. Next"


def test_a_formula_in_the_middle_of_a_sentence_becomes_its_own_block():
    assert streamlit_math("so \\[ x = 1 \\] and more") == "so \n\n$$\nx = 1\n$$\n\n and more"


def test_the_models_own_dollar_blocks_become_proper_blocks():
    assert streamlit_math("$$x(t) = ut \\tag{1}$$") == "$$\nx(t) = ut \\tag{1}\n$$"
    aligned = "$$\\begin{aligned}\nx &= 1 \\\\\ny &= 2\n\\end{aligned}$$"
    assert streamlit_math(aligned) == "$$\n\\begin{aligned} x &= 1 \\\\ y &= 2 \\end{aligned}\n$$"


def test_a_latex_line_break_with_spacing_is_not_read_as_a_new_formula():
    text = "$$\n\\begin{aligned} x &= 1 \\\\[2pt] y &= 2 \\end{aligned}\n$$"
    assert streamlit_math(text) == text


def test_a_latex_comment_does_not_hide_the_rest_of_the_formula():
    assert streamlit_math("\\[\nv = u + at % first equation\n\\]") == "$$\nv = u + at\n$$"


def test_inline_maths_becomes_single_dollars():
    assert streamlit_math("Speed \\(v_0\\) in m s\\(^{-1}\\).") == "Speed $v_0$ in m s$^{-1}$."


def test_the_ai_answer_shown_to_the_student_is_converted():
    answer = make_answer("Why does a projectile follow a curved path?", tutor=lambda q: (REAL_ANSWER, "test-model", None))
    assert blocks_are_well_formed(answer.text) and r"\[" not in answer.text


def test_the_solvers_own_formulas_each_open_and_close_on_their_line():
    # The checked solver writes "$$...$$" lines itself (drawn inline, and verified in the app); none may be left open.
    for question in ("A projectile is fired at 30 m/s at 45°. Find the maximum height, the time of flight and the range.",
                     "A stone is thrown horizontally from a cliff 45 m high at 15 m/s. Find the time of flight and the range.",
                     "A ball is thrown up at 10 m/s from the roof of a 15 m building. Find the maximum height above the ground."):
        text = make_answer(question, tutor=lambda q: (_ for _ in ()).throw(AssertionError("AI called"))).text
        assert "$$" in text and all(line.count("$$") % 2 == 0 for line in text.splitlines()), question
        assert not re.search(r"^\s*\$\$[^$\n]*$", text, flags=re.M), question


def test_a_real_answer_with_numbered_and_aligned_equations_gets_proper_blocks():
    # Groq, 15 Nov 2026: its \tag{1} and \begin{aligned} failed when drawn as inline maths.
    real = (Path(__file__).parent / "data" / "ai_answer_tags_aligned.md").read_text(encoding="utf-8")
    converted = streamlit_math(real)
    assert blocks_are_well_formed(converted)
    tagged = [line for line in converted.splitlines() if r"\tag" in line]
    assert tagged and all("$" not in line for line in tagged)  # each \tag sits inside a block, never inline
