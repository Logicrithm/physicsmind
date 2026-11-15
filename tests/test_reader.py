"""The question reader and the maximum-height solver. Expected values are worked out by hand in each test."""
import math

import pytest

from physicsmind.projectile import solve_max_height
from physicsmind.reader import NOT_MINE, SOLVABLE, UNCLEAR, quantities, normalise, read_question


def height(question):
    reading = read_question(question)
    assert reading.status == SOLVABLE, reading.reasons
    solution = solve_max_height(reading)
    assert solution.ok, solution.problem
    return solution


def expected(u_y, g=9.8):
    return u_y ** 2 / (2 * g)


# --- The two failures found on 14 Nov 2026 ---

def test_an_angled_launch_uses_only_the_upward_part_of_the_speed():
    # Old parser: 45.92 m (it used the full 30 m/s). Right: (30 sin 45°)² / 2g = 22.96 m.
    solution = height("A projectile is launched at 30 m/s at 45 degrees. Find the maximum height.")
    assert solution.rise == pytest.approx(22.959, abs=1e-3)


def test_km_per_hour_is_converted_before_solving():
    # Old parser: 264.49 m (72 treated as m/s). Right: 72 km/h = 20 m/s, 20² / 2g = 20.41 m.
    solution = height("A ball is thrown up at 72 km/h. Find the maximum height.")
    assert solution.rise == pytest.approx(20.408, abs=1e-3)


# --- Questions it must answer, with the right number ---

@pytest.mark.parametrize("question, rise", [
    ("An object is thrown vertically upward with an initial velocity of 20 m/s. Find its maximum height. Take g = 9.8 m/s^2.", expected(20)),
    ("A ball is thrown straight up at 20 m/s. What is the maximum height? (g = 10 m/s²)", 20.0),
    ("How high does a stone go if it is thrown vertically upwards at 15 m/s? Use g = 9.81 m/s2.", expected(15, 9.81)),
    ("A 2 kg ball is thrown straight up at 54 kmph. How high does it go? Take g as 10.", 11.25),
    ("A ball is thrown upward with a speed of 36 km/hr. Find the maximum height reached.", expected(10)),
    ("A ball is projected upward at 25 ms-1. Find the greatest height. g = 10 m s^-2", 31.25),
    ("A ball is thrown up at 1500 cm/s. Find its maximum height.", expected(15)),
    ("A ball is kicked at 25 m/s at 30° to the vertical. Find the maximum height reached.", expected(25 * math.cos(math.radians(30)))),
    ("A ball is kicked at 20 m/s at 40 degrees above the horizontal on a football field. What is the maximum height on this clear day?",
     expected(20 * math.sin(math.radians(40)))),
    ("A shell is fired with a speed of 50 m/s at an angle of elevation of 60°. Find its maximum height. Take g = 10 m/s^2.",
     (50 * math.sin(math.radians(60))) ** 2 / 20),
    ("theta = pi/6, u = 40 m/s. A projectile is fired. Find its maximum height.", expected(20)),
    ("A stone is thrown upward at 15 m/s on the Moon where g = 1.6 m/s^2. Find the max height.", 15 ** 2 / 3.2),
    ("A ball reaches its highest point after 2 s. Find the maximum height.", 0.5 * 9.8 * 4),
    ("A ball thrown upward at 19.6 m/s reaches the top in 2 s. Find the maximum height.", expected(19.6)),
    ("The vertical component of a projectile's initial velocity is 14 m/s. Find the maximum height.", expected(14)),
    ("A ball is thrown upward at 20 m/s. Neglect air resistance. Find the maximum height. g = 10 N/kg", 20.0),
    ("A ball is thrown up with u = 20 and g = 10. Find the maximum height.", 20.0),
    ("A ball is thrown vertically upward at 20 m/s with a = -9.8 m/s^2. Find the maximum height.", expected(20)),
])
def test_answers(question, rise):
    assert height(question).rise == pytest.approx(rise, rel=1e-6)


def test_a_raised_launch_point_gives_the_height_above_the_ground_too():
    solution = height("Find the maximum height reached by a stone thrown up at 10 m/s from the top of a 20 m tall building.")
    assert solution.rise == pytest.approx(expected(10))
    assert solution.above_ground == pytest.approx(20 + expected(10))


def test_a_launch_height_in_another_unit_is_converted():
    solution = height("A ball is thrown upward at 10 m/s from a balcony 500 cm above the ground. Find the maximum height.")
    assert solution.above_ground == pytest.approx(5 + expected(10))


def test_what_was_assumed_and_ignored_is_reported():
    reading = read_question("A 2 kg ball is thrown at 30 m/s at 45 degrees. Find the maximum height.")
    assert any("9.8" in item for item in reading.assumptions)
    assert any("horizontal" in item for item in reading.assumptions)
    assert any("mass" in note for note in reading.notes)


# --- Questions in scope but unclear: no number, and the reason says what is needed ---

@pytest.mark.parametrize("question, needed", [
    ("A ball is thrown at 20 m/s. Find the maximum height.", "which way"),
    ("A ball is thrown at an angle with speed 20 m/s. Find the maximum height.", "angle isn't given"),
    ("A stone is thrown upward at 15 m/s on the Moon. Find the max height.", "value of g"),
    ("A ball is thrown vertically downward at 10 m/s. Find its maximum height.", "downward"),
    ("A stone is dropped from a 20 m tower. Find its maximum height.", "downward"),
    ("A ball is thrown horizontally at 10 m/s from a cliff. Find the maximum height.", "horizontally"),
    ("A ball is thrown at 20 m/s at 30° below the horizontal. Find the maximum height.", "below the horizontal"),
    ("A ball is thrown at 20 m/s at 120 degrees above the horizontal. Find the maximum height.", "between 0° and 90°"),
    ("A ball is thrown vertically at 20 m/s at 30° to the horizontal. Find the maximum height.", "vertically"),
    ("A ball is thrown upward with a velocity of 20. Find the maximum height.", "no unit"),
    ("A ball is thrown up at 20 ms. Find the maximum height.", "milliseconds"),
    ("A ball is thrown up at 20 furlongs per second. Find the maximum height.", "don't recognise the unit"),
    ("A ball is thrown upward at 20 m/s or 25 m/s. Find the maximum height.", "more than one launch speed"),
    ("A ball is thrown upward at 20 m/s. Its speed at the top is 5 m/s. Find the maximum height.", "another speed"),
    ("A ball is thrown upward at -20 m/s. Find the maximum height.", "zero or negative"),
    ("A ball thrown upward at 20 m/s takes 3 s to reach the top. Find the maximum height.", "disagree"),
    ("A ball is thrown upward at 20 m/s and lands 5 m away. Find the maximum height.", "length"),
    ("A ball is thrown upward at 20 m/s for 4 s. Find the maximum height.", "time"),
    ("A ball is thrown upward at 20 m/s. Take g = 9.8 m/s^2 and g = 10 m/s^2. Find the maximum height.", "different values for g"),
    ("A ball is thrown upward at 20 m/s from a pit 5 m deep. Find the maximum height.", "below the ground"),
    ("A ball is thrown upward at twenty metres per second. Find the maximum height.", "launch speed"),
    ("A ball is thrown at 20 m/s with the horizontal component of velocity 12 m/s. Find the maximum height.", "horizontal part"),
])
def test_unclear_questions_get_no_number(question, needed):
    reading = read_question(question)
    assert reading.status == UNCLEAR, reading
    assert any(needed in reason for reason in reading.reasons), reading.reasons
    assert not solve_max_height(reading).ok


# --- Not this solver's question: handed to the AI tutor ---

@pytest.mark.parametrize("question, on_topic", [
    ("Why do objects fall towards Earth? Explain gravity simply.", False),
    ("a car is at speed of 40 km/hr and another one from other direction at 60 km/hr, when will they meet", False),
    ("With what speed must a ball be thrown to reach a maximum height of 20 m?", True),
    ("A ball reaches a maximum height of 20 m. Find its initial velocity.", True),
    ("Find the maximum height and the time taken to reach it for a ball thrown up at 20 m/s.", True),
    ("A ball is thrown at 20 m/s at 30°. Find the maximum height and the range.", True),
    ("A ball is thrown upward at 20 m/s with air resistance. Find the maximum height.", True),
    ("A rocket accelerates upward at 5 m/s^2 for 10 s. Find the maximum height.", True),
    ("A block slides up an incline at 5 m/s. Find the maximum height.", True),
    ("Two balls are thrown upward at 10 m/s and 20 m/s. Find the maximum height of each.", True),
    ("A ball is thrown up at 10 m/s inside a lift moving up at 2 m/s. Find the maximum height.", True),
    ("A pendulum bob moves at 3 m/s at the bottom. Find the maximum height it rises.", True),
])
def test_other_questions_are_not_answered_by_the_solver(question, on_topic):
    reading = read_question(question)
    assert reading.status == NOT_MINE, reading
    assert reading.on_topic is on_topic


# --- Reading quantities ---

@pytest.mark.parametrize("written, kind, si", [
    ("72 km/h", "speed", 20.0), ("54 kmph", "speed", 15.0), ("36 km/hr", "speed", 10.0), ("20 m/s", "speed", 20.0),
    ("20 ms-1", "speed", 20.0), ("20 m s^-1", "speed", 20.0), ("20 metres per second", "speed", 20.0),
    ("9.8 m/s^2", "acceleration", 9.8), ("9.8 m/s²", "acceleration", 9.8), ("10 ms-2", "acceleration", 10.0),
    ("10 N/kg", "acceleration", 10.0), ("500 cm", "length", 5.0), ("2 km", "length", 2000.0), ("3 min", "time", 180.0),
    ("45°", "angle", math.pi / 4), ("30 degrees", "angle", math.pi / 6), ("200 g", "mass", 0.2),
])
def test_units_are_recognised_and_converted(written, kind, si):
    found, problems = quantities(normalise(f"it moves at {written} now"))
    assert not problems
    assert [(q.kind, round(q.value, 9)) for q in found] == [(kind, round(si, 9))]


def test_exponents_inside_units_are_not_read_as_numbers():
    found, _ = quantities(normalise("g = 9.8 m s^-2 and u = 2 x 10^1 m/s"))
    assert [(q.kind, q.value) for q in found] == [("acceleration", 9.8), ("speed", 20.0)]


# --- Fixes from the evaluation set (15 Nov 2026), checked on fresh wording that is NOT in evals/questions.json ---

@pytest.mark.parametrize("question, needed", [
    ("A body is projected vertically with 30 m/s. Find the greatest height.", "up or down"),
    ("A stone is thrown vertically at 12 m/s from the ground. How high does it go?", "up or down"),
    ("A ball is thrown up at 10 m/s from the roof of a building. Find the maximum height above the ground.", "height isn't given"),
    ("A ball is thrown up at 10 m/s off a table. Find the maximum height.", "height isn't given"),
    ("A ball is thrown upward at 15 m/s from the top of a tall tower. Find its maximum height.", "height isn't given"),
    ("A projectile has an initial vertical velocity of 12 m/s downward. Find the maximum height.", "downward"),
])
def test_fixed_gaps_now_ask_instead_of_guessing(question, needed):
    reading = read_question(question)
    assert reading.status == UNCLEAR and needed in " ".join(reading.reasons), reading.reasons
    assert not solve_max_height(reading).ok


def test_vertically_upward_is_still_answered():
    assert height("A ball is thrown vertically upward at 30 m/s. Find the maximum height.").rise == pytest.approx(expected(30))


def test_a_raised_start_with_its_height_is_still_answered():
    solution = height("A ball is thrown up at 10 m/s from the roof of a 15 m building. Find the maximum height above the ground.")
    assert solution.rise == pytest.approx(expected(10)) and solution.above_ground == pytest.approx(15 + expected(10))


def test_from_the_ground_is_not_a_raised_start():
    assert height("A ball is thrown up from the ground at 10 m/s. Find the maximum height.").rise == pytest.approx(expected(10))


def test_vertical_speed_is_the_upward_part_of_the_launch():
    assert height("The vertical speed of a projectile at launch is 12 m/s. Find its maximum height.").rise == pytest.approx(expected(12))


def test_kilometres_per_second_is_a_speed():
    # 0.5 km/s = 500 m/s; on the Moon 500² / (2 × 1.62) = 77,160 m.
    solution = height("A probe is launched straight up at 0.5 km/s on the Moon, where g = 1.62 m/s². Find the maximum height.")
    assert solution.rise == pytest.approx(500 ** 2 / (2 * 1.62))
