"""The AI tutor: free providers tried in order. No paid fallback is configured.

Groq is tried first when a GROQ_API_KEY is set, because its free plan allows far more answers per day (1,000 for
openai/gpt-oss-120b, read from Groq's own rate-limit headers on 15 Nov 2026, with 8,000 tokens a minute) than
OpenRouter's free models (50 per day for the whole account) and its terms say it does not train on what is sent. OpenRouter is the second choice. When a provider is out of free answers or
fails, the next one is tried. Each provider's model can be changed in the settings without touching the code.
"""
from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from .config import setting

NOT_CONFIGURED = "not_configured"   # no key for any provider
LIMIT_REACHED = "limit_reached"     # every provider with a key is out of free answers for now
FAILED = "failed"                   # every provider with a key failed for another reason

SYSTEM_PROMPT = (
    "You are PhysicsMind, a careful physics tutor. Explain clearly at school level unless asked otherwise. "
    "Define symbols, state assumptions, use SI units, and show reasoning. Do not invent facts or claim a "
    "calculation was verified by code. Ask for clarification if needed."
)


@dataclass(frozen=True)
class Provider:
    name: str
    key_setting: str
    model_setting: str
    default_model: str
    base_url: str


PROVIDERS = (
    Provider("Groq", "GROQ_API_KEY", "GROQ_MODEL", "openai/gpt-oss-120b", "https://api.groq.com/openai/v1"),
    Provider("OpenRouter", "OPENROUTER_API_KEY", "OPENROUTER_MODEL", "openrouter/free", "https://openrouter.ai/api/v1"),
)


def _is_limit(exc: Exception) -> bool:
    return getattr(exc, "status_code", None) == 429 or type(exc).__name__ == "RateLimitError"


def _safe(text: str, secret: str) -> str:
    return text.replace(secret, "[REDACTED_API_KEY]") if secret else text


def ask_tutor(question: str, providers=PROVIDERS, make_client=OpenAI, log=print):
    """Returns (answer, model label, error). error is None on success, else NOT_CONFIGURED, LIMIT_REACHED or FAILED.
    Technical details go to the server log with keys removed; the student only sees a plain message."""
    configured = [(p, setting(p.key_setting)) for p in providers]
    configured = [(p, key) for p, key in configured if key]
    if not configured:
        return None, None, NOT_CONFIGURED

    limited = False
    for provider, key in configured:
        model = setting(provider.model_setting, provider.default_model)
        try:
            client = make_client(base_url=provider.base_url, api_key=key, timeout=45, max_retries=1)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}],
                temperature=0.2,
            )
            answer = (response.choices[0].message.content or "").strip()
            if not answer:
                raise ValueError("the provider returned an empty answer")
            used = getattr(response, "model", None) or model
            return answer, f"{used} via {provider.name}", None
        except Exception as exc:  # try the next free provider
            limited = limited or _is_limit(exc)
            log(f"AI tutor: {provider.name} failed: {type(exc).__name__}: {_safe(str(exc), key)[:300]}")
    return None, None, LIMIT_REACHED if limited else FAILED
