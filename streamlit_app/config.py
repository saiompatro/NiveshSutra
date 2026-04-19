"""Runtime configuration helpers for local and hosted Streamlit environments."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:  # pragma: no cover - streamlit is expected at runtime
    st = None


load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


def _streamlit_secret(name: str):
    if st is None:
        return None
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def get_setting(name: str, default: str = "") -> str:
    secret_value = _streamlit_secret(name)
    if secret_value not in (None, ""):
        return str(secret_value)
    return os.getenv(name, default)


def get_required_setting(name: str) -> str:
    value = get_setting(name)
    if value:
        return value
    raise RuntimeError(f"Missing required configuration: {name}")


def get_api_base_url() -> str:
    return get_setting("API_BASE_URL")
