"""Optional OpenRouter-backed tutor. No paid fallback is configured."""
import os
from openai import OpenAI

def ask_tutor(question: str):
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()

    if not api_key:
        return None, None, (
            "AI tutor is not configured yet. Add an OpenRouter key to your local .env file. "
            "The numerical solver works without an API key."
        )

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are PhysicsMind, a careful physics tutor. Explain clearly at "
                        "school level unless asked otherwise. Define symbols, state assumptions, "
                        "use SI units, and show reasoning. Do not invent facts or claim a "
                        "calculation was verified by code. Ask for clarification if needed."
                    )
                },
                {"role": "user", "content": question}
            ],
            temperature=0.2,
        )
        answer = response.choices[0].message.content or ""
        used_model = getattr(response, "model", model)
        return answer, used_model, None
    except Exception as exc:
        # Keep technical error information while ensuring secrets are completely redacted.
        err_msg = str(exc)
        if api_key and api_key in err_msg:
            err_msg = err_msg.replace(api_key, "[REDACTED_API_KEY]")
        return None, model, f"AI provider request failed. Check key, model availability and free quota. Details: {type(exc).__name__}: {err_msg}"
