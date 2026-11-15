"""Settings, read the same way on this computer and online.

On this computer they come from `.env` (loaded by app.py). On Streamlit Community Cloud they come from the app's
Secrets page, which Streamlit also exposes as environment variables; st.secrets is read as a second source in case
a setting is only there. Nothing secret is ever written into the code or the repository.
"""
from __future__ import annotations

import os


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
