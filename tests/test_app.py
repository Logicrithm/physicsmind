"""The real app script, run headless by Streamlit's own test runner. Only questions the solver or the
clarification check answer are used, so nothing here calls the AI tutor or goes online."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def ask(question):
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.chat_input[0].set_value(question).run()
    assert not app.exception
    return app


def replies(app):
    return [m.markdown[0].value for m in app.chat_message if m.name == "assistant"]


def test_the_motion_starter_is_answered_by_the_solver():
    app = AppTest.from_file(APP, default_timeout=60).run()
    next(b for b in app.button if b.key == "starter_Solve a motion problem").click().run()
    assert not app.exception
    assert "**Answer: 20.41 m**" in replies(app)[0]
    assert app.session_state.messages[-1]["response_type"] == "solver"


def test_the_two_questions_that_used_to_be_wrong_are_right_in_the_app():
    assert "22.96 m" in replies(ask("A projectile is launched at 30 m/s at 45 degrees. Find the maximum height."))[0]
    assert "20.41 m" in replies(ask("A ball is thrown up at 72 km/h. Find the maximum height."))[0]


def test_feedback_records_which_part_gave_the_answer(tmp_path, monkeypatch):
    # Point every feedback function at a temporary database, so the real one is never written.
    from physicsmind import feedback
    db = tmp_path / "feedback.db"
    for function in (feedback.init_db, feedback.save_feedback, feedback.feedback_count):
        defaults = list(function.__defaults__)
        defaults[-1] = db
        monkeypatch.setattr(function, "__defaults__", tuple(defaults))
    app = ask("A ball is thrown up at 72 km/h. Find the maximum height.")
    next(b for b in app.button if b.label == "Send feedback").click().run()
    assert not app.exception
    import sqlite3
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT response_type, rating, verification_status FROM response_feedback").fetchall()
    assert rows == [("solver", "helpful", "checked: SymPy result matches the direct formula")]


def test_an_unclear_question_is_answered_with_a_question():
    app = ask("A ball is thrown at 20 m/s. Find the maximum height.")
    assert "which way" in replies(app)[0]
    assert app.session_state.messages[-1]["response_type"] == "clarification"
