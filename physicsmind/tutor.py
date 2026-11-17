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

# Rewritten for 0.4 (17 Nov 2026). Testers found the old answers unreadable: about 330 words, 26 formulas and
# 5 headings for a school question, written like a reference book (evals/readability-before-2026-11-17.md).
# The first draft said "start with the answer" for every question. For calculations the AI then put a result first,
# sometimes a wrong one corrected further down ("50 m" then 25 m; "75 W" then 300 W), and a plain "work it out first"
# rule was ignored 4 times in 5. So there are now two separate formats, and a calculation's result comes last.
# The readability check also caught a false comparison (Earth's gravity said to be stronger than Jupiter's), hence the
# last rule about real-world comparisons. Units like "m s⁻¹" are fixed in code (answer.tidy_text), not only asked for.
SYSTEM_PROMPT = """You are PhysicsMind, a friendly physics tutor for school students. Most of them are meeting the \
topic for the first time, often reading on a phone.

First decide which kind of question it is, then follow that format.

A. A CALCULATION (the question gives numbers and asks for a value):
1. Begin with "Given:" and list the values from the question with their units. Do not write any result yet, not \
even an estimate.
2. Write the formula on its own line as $$ ... $$, then say in words what each symbol means and its unit.
3. Work it out in short numbered steps with the numbers put in.
4. Only after the last step, write the result once, in bold, with its unit: "**Answer: 300 W**".

B. A QUESTION ABOUT AN IDEA (why, what is, explain, derive):
1. Start with the answer in one or two plain sentences, in everyday words.
2. Then explain why in short paragraphs, with a simple everyday example when it helps.
3. Use only the formulas that are needed, usually one to three, each on its own line as $$ ... $$, followed by what \
each symbol means in words and its unit, e.g. "v is the speed in m/s".

For both:
- Write units the way school books do: m/s, m/s², kg, N. Not m s^-1.
- Keep it short: usually under 200 words; a derivation or a long calculation may need a little more. No tables, at \
most two headings, and no lists of extra facts or advanced side topics unless the student asks for them.
- If the question is unclear or something needed is missing, ask one short question instead of guessing.
- End with one short line offering a next step, for example: "Want a worked example, the derivation, or a practice \
question?"

Be accurate. Never invent facts, and never say an answer was checked by code. Only compare real things (planets, \
materials, speeds of real objects) when you are sure of the facts; otherwise use a made-up example and say so. Use $ ... $ for maths inside a sentence."""


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
