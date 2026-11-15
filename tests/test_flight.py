"""Time to the top, time of flight and range (added 15 Nov 2026). Every question here is worded differently from
evals/questions.json, and every expected value is worked out by hand in the test."""
import math

import pytest

from physicsmind.answer import SOLVER, make_answer
from physicsmind.projectile import solve_projectile
from physicsmind.reader import NOT_MINE, RANGE, SOLVABLE, T_FLIGHT, T_TOP, UNCLEAR, read_question

G = 9.8


def solved(question):
    reading = read_question(question)
    assert reading.status == SOLVABLE, reading.reasons
    solution = solve_projectile(reading)
    assert solution.ok, solution.problem
    return reading, solution


def parts(u, degrees):
    return u * math.sin(math.radians(degrees)), u * math.cos(math.radians(degrees))


# --- Answers ---

def test_range_on_level_ground_matches_the_textbook_formula():
    # R = u² sin 2θ / g = 80² × sin 90° / 9.8 = 653.06 m
    reading, solution = solved("A shell is fired from a gun at 80 m/s at 45 degrees. How far away does it land?")
    assert reading.asks == [RANGE]
    assert solution.range == pytest.approx(80 ** 2 / G)


def test_time_of_flight_on_level_ground_is_twice_the_time_to_the_top():
    uy, _ = parts(25, 30)  # 12.5 m/s, so T = 2 × 12.5 / 9.8 = 2.551 s
    reading, solution = solved("A stone is projected at 25 m/s at 30° to the horizontal. Calculate how long it stays in the air.")
    assert reading.asks == [T_FLIGHT]
    assert solution.time_of_flight == pytest.approx(2 * uy / G)


def test_time_of_ascent():
    _, solution = solved("A ball is thrown at 20 m/s at 30° above the horizontal. Find the time of ascent.")
    assert solution.time_to_top == pytest.approx(10 / G)  # u_y = 10 m/s


def test_from_a_building_the_positive_root_is_used():
    # -25 = 20T - 5T² gives T² - 4T - 5 = 0, so T = 5 s (the other root, -1 s, is before the launch).
    _, solution = solved("A ball is thrown upward at 20 m/s from the edge of a 25 m high building. "
                         "How long does it take to reach the ground below? Take g = 10 m/s².")
    assert solution.time_of_flight == pytest.approx(5.0)


def test_horizontal_throw_from_a_height():
    # Falls 1.8 m from rest vertically: T = √(2 × 1.8 / 9.8) = 0.606 s
    _, solution = solved("A dart is thrown horizontally at 10 m/s from a height of 1.8 m. How long until it hits the floor?")
    assert solution.time_of_flight == pytest.approx(math.sqrt(2 * 1.8 / G))


def test_horizontal_throw_where_does_it_land():
    # R = 10 × √(2 × 2 / 9.8) = 6.389 m
    _, solution = solved("A ball is thrown horizontally at 10 m/s off a 2 m wall. Where does it land?")
    assert solution.range == pytest.approx(10 * math.sqrt(4 / G))


def test_several_answers_at_once_and_the_time_to_reach_it():
    uy, ux = parts(30, 45)
    reading, solution = solved("A projectile is launched at 30 m/s at 45°. Find the maximum height, time to reach it and range.")
    assert reading.asks == ["height", T_TOP, RANGE]
    assert solution.rise == pytest.approx(uy ** 2 / (2 * G))
    assert solution.time_to_top == pytest.approx(uy / G)
    assert solution.range == pytest.approx(ux * 2 * uy / G)


def test_how_far_from_the_thrower_does_it_hit_the_ground():
    uy, ux = parts(18, 40)
    _, solution = solved("A ball is thrown at 18 m/s at 40° to the horizontal. How far from the thrower does it hit the ground?")
    assert solution.range == pytest.approx(ux * 2 * uy / G)


def test_coming_back_to_the_thrower_from_the_ground():
    _, solution = solved("A ball is thrown up at 12 m/s. After how much time does it come back to the thrower?")
    assert solution.time_of_flight == pytest.approx(2 * 12 / G)


def test_an_angled_throw_from_a_cliff():
    # u_y = 15 sin 50°, u_x = 15 cos 50°, lands 12 m below: T = (u_y + √(u_y² + 2·9.8·12)) / 9.8
    uy, ux = parts(15, 50)
    T = (uy + math.sqrt(uy ** 2 + 2 * G * 12)) / G
    _, solution = solved("From the top of a 12 m cliff a stone is thrown at 15 m/s at 50° above the horizontal. "
                         "Find how long it is in the air and how far from the foot of the cliff it lands.")
    assert solution.time_of_flight == pytest.approx(T) and solution.range == pytest.approx(ux * T)


def test_a_launch_speed_after_hits_is_still_the_launch_speed():
    # Fixed on 15 Nov 2026: "hits a golf ball at 20 m/s" was read as a landing speed (eval E21).
    _, solution = solved("A batter hits a baseball at 35 m/s at 30° above the horizontal. Find the range.")
    assert solution.range == pytest.approx(35 ** 2 * math.sin(math.radians(60)) / G)


# --- Never a number when it would be a guess ---

@pytest.mark.parametrize("question, needed", [
    ("A ball is thrown straight up at 15 m/s. How far does it travel horizontally?", "no horizontal range"),
    ("A marble is thrown horizontally at 4 m/s. Find the time of flight.", "height it is thrown from"),
    ("A ball is thrown horizontally at 6 m/s from a 5 m high balcony. Find its maximum height.", "never rises"),
    ("A ball is thrown horizontally at 6 m/s off a balcony. How far from the building does it land?", "height isn't given"),
    ("The vertical part of a ball's launch velocity is 9 m/s. How far away does it land?", "sideways part"),
    ("A ball is thrown at 20 m/s at 30° above the horizontal from a 10 m cliff. Find the time to return to the launch height.",
     "back at that height"),
    ("A ball is thrown at 15 m/s at 30° above the horizontal. Find the time of flight. Take g = 10 m/s². Use g = 9.8 m/s².",
     "different values for g"),
    ("A ball is kicked at 25 m/s at 30° above the horizontal and stays in the air for 6 s. Find the range.", "time"),
])
def test_unclear_flight_questions_get_no_number(question, needed):
    reading = read_question(question)
    assert reading.status == UNCLEAR, reading
    assert any(needed in reason for reason in reading.reasons), reading.reasons
    assert not solve_projectile(reading).ok


@pytest.mark.parametrize("question", [
    "A ball is thrown at 20 m/s at 30° above the horizontal. Find its speed when it lands.",
    "A ball is thrown at 20 m/s at 30° below the horizontal from a cliff 40 m high. Find the time of flight.",
    "A stone is dropped from a 20 m tower. How long does it take to hit the ground?",
    "A ball is thrown at 20 m/s at 40° and lands on a platform 3 m high. Find the range.",
    "A ball is thrown at 25 m/s at 50°. Find the maximum horizontal range possible.",
    "A football is kicked at 20 m/s at 35° to the horizontal. How long does it take to reach a height of 5 m?",
    # Fixed on 15 Nov 2026: this was answered with the full range, but it asks for the distance at the top.
    "A ball is thrown at 30 m/s at 60° to the horizontal. Find the time it takes to reach its maximum height and "
    "the horizontal distance at that moment.",
    "Find the horizontal distance travelled in 2 s by a ball thrown at 10 m/s at 30°.",
])
def test_flight_questions_it_does_not_cover_go_to_the_ai(question):
    reading = read_question(question)
    assert reading.status == NOT_MINE, reading
    assert solve_projectile(reading).ok is False


# --- What the student sees ---

def test_the_explanation_shows_each_step_and_every_answer():
    answer = make_answer("A stone is thrown horizontally from a cliff 45 m high with a speed of 15 m/s. "
                         "Find the time taken to reach the ground and how far from the cliff it lands. Take g = 10 m/s².",
                         tutor=lambda q: pytest.fail("the AI must not be called"))
    assert answer.response_type == SOLVER
    text = answer.text
    assert "Thrown horizontally" in text and "u_y = 0" in text
    assert r"T = \sqrt{\frac{2h_0}{g}} = \sqrt{\frac{2 \times 45}{10}} = 3.00" in text  # not "0 + √(0² + ...)"
    assert "- Time of flight: **3.00 s**" in text and "- Horizontal range: **45.00 m**" in text
    assert "It lands on the ground, 45 m below where it was launched." in text
    assert "the quadratic formula gives the same time of flight" in text and "R = u_x × T gives the same range" in text


def test_a_range_only_answer_explains_the_time_it_needs():
    text = make_answer("A ball is kicked at 20 m/s at 30° above the horizontal. Find the range.",
                       tutor=lambda q: pytest.fail("the AI must not be called")).text
    assert "**Time in the air (needed for the range)**" in text
    assert "u_x = u\\cos\\theta" in text
    assert f"- Horizontal range: **{20 ** 2 * math.sin(math.radians(60)) / G:.2f} m**" in text
    assert "Time of flight: **" not in text  # not asked, so not listed as an answer


def test_a_height_only_answer_is_unchanged():
    text = make_answer("A ball is thrown vertically upward at 20 m/s. Find the maximum height.").text
    assert "**Answer: 20.41 m** (above the launch point)" in text and "**Answer**\n" not in text


# --- Questions about understanding a formula go to the AI tutor (found in the running app, 15 Nov 2026) ---

@pytest.mark.parametrize("question", [
    "Explain step by step how the range formula R = u^2 sin(2θ)/g is derived for a projectile.",
    "Derive the expression for the maximum height of a projectile.",
    "Why is the time of flight twice the time to reach the top?",
    "What is the formula for the horizontal range of a projectile?",
    "Prove that the range is greatest at 45 degrees.",
    "How does the maximum height depend on the launch angle?",
])
def test_asking_how_a_formula_works_is_not_turned_into_a_calculation(question):
    reading = read_question(question)
    assert reading.status == NOT_MINE and "formula" in reading.reasons[0], reading


def test_a_calculation_that_mentions_an_equation_is_still_solved():
    _, solution = solved("Using the equation v² = u² + 2as, find the maximum height of a ball thrown straight up at 14 m/s.")
    assert solution.rise == pytest.approx(14 ** 2 / (2 * G))
