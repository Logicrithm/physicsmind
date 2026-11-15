"""The real app script, run headless by Streamlit's own test runner. conftest.py removes every key, so nothing
here can call an AI provider, write online, or touch the real feedback file."""
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


def test_feedback_records_which_part_gave_the_answer_and_the_version():
    # conftest.py points the feedback file at a temporary one, so the real physicsmind.db is never written.
    import sqlite3
    from physicsmind import feedback
    from physicsmind.version import app_version
    app = ask("A ball is thrown up at 72 km/h. Find the maximum height.")
    next(b for b in app.button if b.label == "Send feedback").click().run()
    assert not app.exception
    with sqlite3.connect(feedback.DEFAULT_DB) as conn:
        rows = conn.execute("SELECT response_type, rating, verification_status, app_version "
                            "FROM response_feedback").fetchall()
    assert rows == [("solver", "helpful", "checked: SymPy result matches the direct formula", app_version())]
    assert any("saved on this computer" in c.value for c in app.caption)


def test_the_privacy_note_is_shown_before_anything_is_asked():
    app = AppTest.from_file(APP, default_timeout=60).run()
    assert any("don’t include your name" in m.value for m in app.markdown)


def test_when_the_visit_has_no_ai_questions_left_the_ai_is_not_called(monkeypatch):
    monkeypatch.setenv("AI_QUESTIONS_PER_VISIT", "0")
    app = ask("Explain the difference between voltage and current.")
    assert "AI-tutor questions for this visit" in replies(app)[0]
    assert app.session_state.messages[-1]["response_type"] == "ai_limit"
    assert app.session_state.ai_used == 0


def test_an_unclear_question_is_answered_with_a_question():
    app = ask("A ball is thrown at 20 m/s. Find the maximum height.")
    assert "which way" in replies(app)[0]
    assert app.session_state.messages[-1]["response_type"] == "clarification"


def test_the_chat_box_and_feedback_note_have_length_limits():
    from physicsmind.answer import MAX_QUESTION_CHARS
    app = ask("A ball is thrown up at 72 km/h. Find the maximum height.")
    assert app.chat_input[0].proto.max_chars == MAX_QUESTION_CHARS
    assert app.text_input[0].proto.max_chars == 500


def test_after_the_visit_feedback_limit_no_more_forms_are_shown():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.session_state["feedback_sent"] = 40
    app.chat_input[0].set_value("A ball is thrown up at 72 km/h. Find the maximum height.").run()
    assert not app.exception
    assert not [b for b in app.button if b.label == "Send feedback"]
    assert any("reached the limit for one visit" in c.value for c in app.caption)


def test_the_privacy_note_says_general_questions_go_to_an_outside_ai():
    app = AppTest.from_file(APP, default_timeout=60).run()
    assert any("outside AI service" in m.value for m in app.markdown)


def test_public_site_settings_hide_error_details_and_developer_menu():
    import tomllib
    settings = tomllib.loads((Path(APP).parent / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    assert settings["client"] == {"showErrorDetails": "none", "toolbarMode": "viewer"}
    assert "enableCORS" not in settings["server"]  # Streamlit's protective default stays on
