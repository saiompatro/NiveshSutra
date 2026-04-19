"""
Auth helpers for Streamlit session management.

Session state keys:
  st.session_state["session"]  → Supabase Session object (access_token, refresh_token)
  st.session_state["user"]     → Supabase User object (id, email)
  st.session_state["profile"]  → dict from profiles table
"""
import streamlit as st
from supabase_client import get_anon_client, get_authed_client


def login(email: str, password: str) -> tuple[bool, str]:
    """Sign in. Returns (success, error_message)."""
    try:
        client = get_anon_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.session and response.user:
            st.session_state["session"] = response.session
            st.session_state["user"] = response.user
            _load_profile(response.user.id, response.session.access_token)
            return True, ""
        return False, "Invalid credentials"
    except Exception as e:
        return False, str(e)


def signup(email: str, password: str) -> tuple[bool, str]:
    """Sign up a new user. Returns (success, error_message)."""
    try:
        client = get_anon_client()
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user:
            # Auto-login if session available (email confirmation disabled)
            if response.session:
                st.session_state["session"] = response.session
                st.session_state["user"] = response.user
                _load_profile(response.user.id, response.session.access_token)
            else:
                return True, "CHECK_EMAIL"
            return True, ""
        return False, "Signup failed"
    except Exception as e:
        return False, str(e)


def logout():
    """Clear session state."""
    for key in ["session", "user", "profile", "selected_stock"]:
        st.session_state.pop(key, None)


def require_auth():
    """
    Call at the top of every protected page.
    Redirects to app.py if session is missing.
    """
    if "session" not in st.session_state or "user" not in st.session_state:
        st.switch_page("app.py")


def get_access_token() -> str:
    return st.session_state["session"].access_token


def get_user_id() -> str:
    return st.session_state["user"].id


def get_profile() -> dict:
    return st.session_state.get("profile", {})


def _load_profile(user_id: str, access_token: str):
    try:
        client = get_authed_client(access_token)
        result = client.table("profiles").select("*").eq("id", user_id).single().execute()
        st.session_state["profile"] = result.data or {}
    except Exception:
        st.session_state["profile"] = {}


def refresh_profile():
    """Re-fetch profile from DB and update session state."""
    if "user" in st.session_state and "session" in st.session_state:
        _load_profile(get_user_id(), get_access_token())
