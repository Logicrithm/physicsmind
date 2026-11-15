"""PhysicsMind uses only its own keys: from its .env file locally, or the host's Secrets page online. A key with
the same name inherited from Windows (another project's Groq key) is ignored."""
import os

from physicsmind import config
from physicsmind.config import setting, use_only_own_keys


def test_a_groq_key_inherited_from_windows_is_not_used(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY=physicsmind-openrouter\n", encoding="utf-8")
    monkeypatch.setenv("GROQ_API_KEY", "other-project-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "physicsmind-openrouter")
    assert use_only_own_keys(env) == ["GROQ_API_KEY"]
    assert setting("GROQ_API_KEY") == ""
    assert setting("OPENROUTER_API_KEY") == "physicsmind-openrouter"


def test_an_empty_line_in_env_still_counts_as_not_set(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("GROQ_API_KEY=\n", encoding="utf-8")
    monkeypatch.setenv("GROQ_API_KEY", "other-project-key")
    assert use_only_own_keys(env) == ["GROQ_API_KEY"]
    assert "GROQ_API_KEY" not in os.environ


def test_physicsminds_own_groq_key_in_env_is_kept(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("GROQ_API_KEY=physicsmind-groq\n", encoding="utf-8")
    monkeypatch.setenv("GROQ_API_KEY", "physicsmind-groq")
    assert use_only_own_keys(env) == []
    assert setting("GROQ_API_KEY") == "physicsmind-groq"


def test_online_a_key_from_the_secrets_page_is_kept(tmp_path, monkeypatch):
    # The host has no .env file; its Secrets page values also appear as environment variables.
    monkeypatch.setattr(config, "_streamlit_secret", lambda name: "hosted-key" if name == "GROQ_API_KEY" else "")
    monkeypatch.setenv("GROQ_API_KEY", "hosted-key")
    assert use_only_own_keys(tmp_path / "missing.env") == []
    assert setting("GROQ_API_KEY") == "hosted-key"


def test_ordinary_settings_are_left_alone(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_QUESTIONS_PER_VISIT", "3")
    use_only_own_keys(tmp_path / "missing.env")
    assert config.whole_number("AI_QUESTIONS_PER_VISIT", 10) == 3


def test_a_bad_allowance_falls_back_to_the_default(monkeypatch):
    monkeypatch.setenv("AI_QUESTIONS_PER_VISIT", "lots")
    assert config.whole_number("AI_QUESTIONS_PER_VISIT", 10) == 10
    monkeypatch.setenv("AI_QUESTIONS_PER_VISIT", "-2")
    assert config.whole_number("AI_QUESTIONS_PER_VISIT", 10) == 10
