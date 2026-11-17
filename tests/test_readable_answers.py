"""0.4: AI answers a school student can read. Testers reported unreadable answers (the only two real reports by
16 Nov 2026); these tests guard the parts that can be checked without calling the AI: the instructions, the clean-up
of the AI's writing habits, the measuring tool, the feedback choice, and which questions reach the AI at all."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from evals.readability import measure
from physicsmind.answer import AI_TUTOR, make_answer, tidy_text
from physicsmind.reader import NOT_MINE, SOLVABLE, read_question
from physicsmind.tutor import SYSTEM_PROMPT

APP = str(Path(__file__).resolve().parent.parent / "app.py")


# --- The instructions ---

def test_the_instructions_ask_for_short_plain_answers_for_school_students():
    for rule in ("school students", "under 200 words", "No tables", "m/s, m/s², kg, N", "what each symbol means",
                 "ask one short question instead of guessing", "Want a worked example"):
        assert rule in SYSTEM_PROMPT, rule


def test_a_calculation_lists_what_is_given_first_and_gives_its_result_only_at_the_end():
    # Before this rule the AI opened with a result, sometimes wrong ("75 W", then 300 W further down).
    calculation = SYSTEM_PROMPT.split("A. A CALCULATION")[1].split("B. A QUESTION ABOUT AN IDEA")[0]
    assert 'Begin with "Given:"' in calculation
    assert "Do not write any result yet" in calculation
    assert "Only after the last step, write the result once, in bold" in calculation


def test_the_instructions_still_forbid_invented_facts_and_claims_of_checking():
    assert "Never invent facts" in SYSTEM_PROMPT and "never say an answer was checked by code" in SYSTEM_PROMPT
    assert "Only compare real things" in SYSTEM_PROMPT   # Earth's gravity was once said to be stronger than Jupiter's


# --- Cleaning up the AI's writing habits ---

def test_latex_style_quotes_become_proper_quotes():
    assert tidy_text("a “diluted’’ field and ``this'' word") == "a “diluted” field and “this” word"


def test_an_unclosed_star_at_the_start_of_a_line_becomes_a_list_item():
    assert tidy_text("*Mass $m$ in kg\n*Speed $v$ in m/s") == "- Mass $m$ in kg\n- Speed $v$ in m/s"


def test_an_italic_note_with_a_space_after_the_first_star_is_mended():
    assert tidy_text("* $a$ is the acceleration (m/s²).*") == "*$a$ is the acceleration (m/s²).*"


def test_real_italics_bold_and_list_items_are_left_alone():
    text = "*Everyday example:* a car.\n**Answer: 25 m**\n* $g$ – gravity\n- $m$ – mass"
    assert tidy_text(text) == text


def test_university_style_units_become_school_units():
    assert tidy_text("speed in m s⁻¹, acceleration in m s⁻², 15 km h⁻¹") == "speed in m/s, acceleration in m/s², 15 km/h"
    assert tidy_text(r"$a = 2\ \text{m s}^{-2}$ and $\mathrm{m\,s^{-1}}$") == r"$a = 2\ \text{m/s}^2$ and $\mathrm{m/s}$"
    assert tidy_text("launch speed (m\u202fs$^{-1}$)") == "launch speed (m/s)"


def test_units_that_are_not_speeds_are_left_alone():
    text = "G = 6.67 × 10⁻¹¹ N m² kg⁻², a mass in kg and a time in ms"
    assert tidy_text(text) == text


def test_the_ai_answer_a_student_sees_is_cleaned_up():
    answer = make_answer("Explain momentum in simple words.",
                         tutor=lambda q: ("*Mass in kg\nspeed in m s⁻¹, a “key’’ idea.", "test-model", None))
    assert answer.response_type == AI_TUTOR
    assert answer.text == "- Mass in kg\nspeed in m/s, a “key” idea."


# --- Questions that are not about something thrown go to the AI ---

def test_a_braking_car_is_not_mistaken_for_a_projectile():
    # Found by the 0.4 calculation probe: the reply asked which way the car is thrown.
    reading = read_question("A car slows from 20 m/s to rest in 4 s. How far does it travel while stopping?")
    assert reading.status == NOT_MINE and not reading.on_topic


def test_straight_line_flight_and_distance_questions_go_to_the_ai():
    for question in ("A train accelerates from rest at 1 m/s² for 30 s. How far does it travel?",
                     "A cyclist rides at 5 m/s for 2 minutes. What distance does she cover?"):
        assert read_question(question).status == NOT_MINE, question


def test_thrown_and_launched_objects_still_reach_the_checked_solver():
    for question in ("A ball is thrown at 20 m/s at 30 degrees. Find the range.",
                     "A projectile is given 20 m/s at 45°. How far away does it land?",
                     "A stone is thrown horizontally at 10 m/s from a 20 m cliff. How long is it in the air?",
                     "A football is kicked at 15 m/s at 40° to the horizontal. Find the time of flight."):
        assert read_question(question).status == SOLVABLE, question


# --- Measuring readability ---

def test_measure_counts_words_formulas_and_the_closing_offer():
    text = ("Speed is how fast something moves.\n\n$$\nv = \\frac{d}{t}\n$$\n\nHere $v$ is the speed in m/s.\n\n"
            "Want a worked example?")
    m = measure(text)
    assert m["formulas"] == 2 and m["tables"] == 0 and m["headings"] == 0
    assert m["offer"] and m["blocks_ok"]
    # Words of two letters or more, formulas left out: 6 + "Here is the speed in" (5) + "Want worked example" (3).
    assert m["words"] == 14


def test_measure_spots_broken_maths_blocks_tables_and_headings():
    m = measure("## Title\n\n$$ v = d/t $$\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nThe end.")
    assert not m["blocks_ok"] and m["tables"] == 1 and m["headings"] == 1 and not m["offer"]


def test_a_horizontal_rule_is_not_counted_as_a_table():
    assert measure("One idea.\n\n---\n\nAnother idea.")["tables"] == 0


# --- Feedback ---

def test_students_can_report_an_answer_that_is_hard_to_read_or_too_long():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.chat_input[0].set_value("A ball is thrown straight up at 20 m/s. Find its maximum height.").run()
    assert not app.exception
    options = app.selectbox[0].options
    assert options[0] == "No issue"
    assert "Hard to read / looks broken" in options and "Too long" in options
    assert all(len(option) <= 100 for option in options)   # the database allows up to 100 characters
