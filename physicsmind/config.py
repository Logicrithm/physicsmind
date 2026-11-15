"""Settings, read the same way on this computer and online.

On this computer they come from `.env` (loaded by app.py). On Streamlit Community Cloud they come from the app's
Secrets page, which Streamlit also exposes as environment variables; st.secrets is read as a second source in case
a setting is only there. Nothing secret is ever written into the code or the repository. API keys inherited from
Windows are ignored (use_only_own_keys), so PhysicsMind never uses another project's key.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
# Keys that must belong to PhysicsMind itself. A key with the same name set in Windows for another project (the
# Groq key of another project, found on 15 Nov 2026) must never be used, or this app would spend that project's allowance.
OWN_KEYS = ("GROQ_API_KEY", "OPENROUTER_API_KEY", "SUPABASE_URL", "SUPABASE_KEY")


def use_only_own_keys(env_file: Path = ENV_FILE) -> list[str]:
    """Forget, for this running app only, any of OWN_KEYS that came neither from PhysicsMind's .env file nor from
    the host's Secrets page. Windows itself is not changed. Returns the names that were dropped."""
    own = dotenv_values(env_file) if Path(env_file).is_file() else {}
    dropped = []
    for name in OWN_KEYS:
        if name in os.environ and not str(own.get(name) or "").strip() and not _streamlit_secret(name):
            del os.environ[name]
            dropped.append(name)
    return dropped


def setting(name: str, default: str = "") -> str:
    return os.getenv(name, "").strip() or _streamlit_secret(name) or default


def _streamlit_secret(name: str) -> str:
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:  # no secrets file locally, or not running inside Streamlit
        return ""


def whole_number(name: str, default: int) -> int:
    """A setting that must be a whole number of 0 or more; anything else falls back to the default."""
    try:
        value = int(setting(name, str(default)))
    except ValueError:
        return default
    return value if value >= 0 else default
