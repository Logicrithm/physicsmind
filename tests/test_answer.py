"""Who answers: the checked solver, a clarification, or the AI tutor. The AI is always replaced here."""
from physicsmind.answer import AI_TUTOR, AI_UNAVAILABLE, CLARIFICATION, SOLVER, make_answer


class FakeTutor:
    def __init__(self, reply=("An answer from the AI.", "test-model", None)):
        self.reply, self.questions = reply, []

    def __call__(self, question):
        self.questions.append(question)
        return self.reply


def test_a_clear_maximum_height_question_is_solved_without_the_ai():
    tutor = FakeTutor()
    answer = make_answer("A projectile is launched at 30 m/s at 45 degrees. Find the maximum height.", tutor)
    assert answer.response_type == SOLVER
    assert "22.96 m" in answer.text
    assert "45° from the horizontal" in answer.text
    assert "taken from the horizontal (the usual convention)" in answer.text
    assert "Checked:" in answer.text and answer.verification.startswith("checked")
    assert tutor.questions == []


def test_the_answer_shows_the_unit_conversion():
    answer = make_answer("A ball is thrown up at 72 km/h. Find the maximum height.", FakeTutor())
    assert "72 km/h = 20 m/s" in answer.text
    assert "20.41 m" in answer.text


def test_a_raised_start_gives_both_heights():
    answer = make_answer("A stone is thrown up at 10 m/s from a 20 m tall building. Find the maximum height.", FakeTutor())
    assert "5.10 m above its launch point" in answer.text and "25.10 m above the ground" in answer.text


def test_an_unclear_question_gets_a_question_back_and_no_number_or_ai_call():
    tutor = FakeTutor()
    answer = make_answer("A ball is thrown at 20 m/s. Find the maximum height.", tutor)
    assert answer.response_type == CLARIFICATION
    assert "which way" in answer.text
    assert "20.41" not in answer.text and "Answer" not in answer.text
    assert tutor.questions == []
    # Found in the running app on 15 Nov: the summary claimed "straight up" while asking which way.
    assert "Direction: not clear yet" in answer.text and "straight up\n" not in answer.text


def test_units_are_shown_the_way_a_textbook_writes_them():
    answer = make_answer("A ball is thrown straight up at 54 kmph. Find the maximum height. Take g = 9.8 m/s^2.", FakeTutor())
    assert "g = 9.8 m/s²" in answer.text and "m/s^2" not in answer.text
    assert "54 km/h = 15 m/s" in answer.text


def test_other_questions_go_to_the_ai_and_are_labelled_unchecked():
    tutor = FakeTutor()
    answer = make_answer("Explain the difference between voltage and current.", tutor)
    assert answer.response_type == AI_TUTOR and answer.source == "test-model"
    assert "not independently verified" in answer.verification
    assert answer.text == "An answer from the AI."
    assert tutor.questions == ["Explain the difference between voltage and current."]


def test_a_height_question_the_solver_cannot_handle_says_why_before_the_ai_answer():
    answer = make_answer("A ball is thrown upward at 20 m/s with air resistance. Find the maximum height.", FakeTutor())
    assert answer.response_type == AI_TUTOR
    assert answer.text.startswith("*The checked solver doesn't answer this one because it involves air resistance")
    assert "An answer from the AI." in answer.text


def test_without_an_ai_key_the_reply_says_so():
    answer = make_answer("Why is the sky blue?", FakeTutor((None, None, "AI tutor is not configured yet.")))
    assert answer.response_type == AI_UNAVAILABLE
    assert "OpenRouter API key" in answer.text
