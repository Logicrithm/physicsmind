"""The AI tutor's free providers: order, falling back, and what happens when they run out. No network is used."""
from types import SimpleNamespace

from physicsmind.tutor import FAILED, LIMIT_REACHED, NOT_CONFIGURED, PROVIDERS, ask_tutor


class Limited(Exception):
    status_code = 429


class FakeClients:
    """Stands in for openai.OpenAI. `script` maps a provider's address to an answer or an exception."""

    def __init__(self, script):
        self.script, self.calls = script, []

    def __call__(self, base_url, api_key, timeout, max_retries):
        def create(model, messages, temperature):
            self.calls.append((base_url, model, api_key))
            outcome = self.script[base_url]
            if isinstance(outcome, Exception):
                raise outcome
            return SimpleNamespace(model=model, choices=[SimpleNamespace(message=SimpleNamespace(content=outcome))])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


GROQ, OPENROUTER = (p.base_url for p in PROVIDERS)


def test_with_no_key_nothing_is_called():
    clients = FakeClients({})
    assert ask_tutor("Why is the sky blue?", make_client=clients) == (None, None, NOT_CONFIGURED)
    assert clients.calls == []


def test_groq_is_asked_first_when_it_has_a_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o-key")
    clients = FakeClients({GROQ: "Rayleigh scattering.", OPENROUTER: "unused"})
    assert ask_tutor("Why is the sky blue?", make_client=clients) == (
        "Rayleigh scattering.", "openai/gpt-oss-120b via Groq", None)
    assert [call[0] for call in clients.calls] == [GROQ]


def test_when_groq_is_out_of_free_answers_openrouter_answers(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o-key")
    logged = []
    clients = FakeClients({GROQ: Limited("rate limit for g-key"), OPENROUTER: "Rayleigh scattering."})
    answer, model, error = ask_tutor("Why is the sky blue?", make_client=clients, log=logged.append)
    assert (answer, model, error) == ("Rayleigh scattering.", "openrouter/free via OpenRouter", None)
    assert "Groq failed" in logged[0] and "g-key" not in logged[0]  # keys never reach the log


def test_only_openrouter_works_as_before(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "o-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model:free")
    clients = FakeClients({OPENROUTER: "An answer."})
    assert ask_tutor("q", make_client=clients) == ("An answer.", "some/model:free via OpenRouter", None)


def test_all_out_of_free_answers_is_reported_as_a_limit(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o-key")
    clients = FakeClients({GROQ: Limited(), OPENROUTER: Limited()})
    assert ask_tutor("q", make_client=clients, log=lambda _: None) == (None, None, LIMIT_REACHED)


def test_other_failures_and_empty_answers_are_reported_as_failed(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "g-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o-key")
    clients = FakeClients({GROQ: ConnectionError("down"), OPENROUTER: "   "})
    assert ask_tutor("q", make_client=clients, log=lambda _: None) == (None, None, FAILED)
