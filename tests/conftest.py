"""Applies to every test: the real feedback file, the online database and the AI providers are out of reach."""
import pytest

from physicsmind import feedback

KEYS = ("SUPABASE_URL", "SUPABASE_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "AI_QUESTIONS_PER_VISIT")


@pytest.fixture(autouse=True)
def keep_real_data_and_keys_out(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback, "DEFAULT_DB", tmp_path / "feedback.db")
    for name in KEYS:
        monkeypatch.delenv(name, raising=False)
    # app.py loads .env when it starts; in tests it must not, or the real keys would come back.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setattr("physicsmind.config._streamlit_secret", lambda name: "")
    yield
