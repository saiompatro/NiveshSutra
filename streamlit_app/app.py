"""
NiveshSutra — Streamlit Entry Point.

Flow:
  1. Not logged in   → show Login / Sign Up tabs
  2. Logged in, onboarding incomplete → show risk questionnaire
  3. Logged in + onboarded → navigate to Dashboard
"""
import sys
from pathlib import Path

# Ensure streamlit_app dir is on path so sibling modules are importable
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from auth import login, signup, logout, get_profile, refresh_profile, get_access_token, get_user_id
from utils import compute_risk_profile
from supabase_client import get_authed_client

st.set_page_config(
    page_title="NiveshSutra",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar logout (visible only when logged in)
# ---------------------------------------------------------------------------

def render_sidebar():
    profile = get_profile()
    with st.sidebar:
        st.markdown("## 📈 NiveshSutra")
        st.markdown("---")
        st.markdown(f"**{st.session_state['user'].email}**")
        risk = profile.get("risk_profile", "—")
        st.caption(f"Risk profile: {risk.capitalize() if risk else '—'}")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()


# ---------------------------------------------------------------------------
# Login / Signup
# ---------------------------------------------------------------------------

def render_auth():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 📈 NiveshSutra")
        st.markdown("*AI-powered Indian equity wealth management*")
        st.markdown("---")

        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    with st.spinner("Logging in…"):
                        ok, err = login(email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(f"Login failed: {err}")

        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="su_email")
                new_pass = st.text_input("Password", type="password", key="su_pass")
                new_pass2 = st.text_input("Confirm password", type="password", key="su_pass2")
                submitted2 = st.form_submit_button("Create account", use_container_width=True)
            if submitted2:
                if not new_email or not new_pass:
                    st.error("Please fill in all fields.")
                elif new_pass != new_pass2:
                    st.error("Passwords do not match.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating account…"):
                        ok, msg = signup(new_email, new_pass)
                    if ok and msg == "CHECK_EMAIL":
                        st.success("Account created! Check your email to confirm, then log in.")
                    elif ok:
                        st.rerun()
                    else:
                        st.error(f"Signup failed: {msg}")


# ---------------------------------------------------------------------------
# Onboarding — 5-question risk questionnaire
# ---------------------------------------------------------------------------

QUESTIONS = [
    {
        "q": "1. What is your primary investment goal?",
        "options": [
            ("Preserve capital with minimal risk", 1),
            ("Steady income with moderate growth", 2),
            ("Long-term capital growth", 3),
        ],
    },
    {
        "q": "2. How long is your investment horizon?",
        "options": [
            ("Less than 2 years", 1),
            ("2–5 years", 2),
            ("More than 5 years", 3),
        ],
    },
    {
        "q": "3. How would you react to a 20% portfolio drop?",
        "options": [
            ("Sell immediately to cut losses", 1),
            ("Wait and see if it recovers", 2),
            ("Buy more at the lower price", 3),
        ],
    },
    {
        "q": "4. What percentage of your savings is this investment?",
        "options": [
            ("More than 75%", 1),
            ("25–75%", 2),
            ("Less than 25%", 3),
        ],
    },
    {
        "q": "5. How familiar are you with equity markets?",
        "options": [
            ("Not familiar", 1),
            ("Some knowledge", 2),
            ("Experienced investor", 3),
        ],
    },
]


def render_onboarding():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## Welcome to NiveshSutra 🎯")
        st.markdown(
            "Answer 5 quick questions so we can personalise signals and "
            "portfolio recommendations for you."
        )
        st.markdown("---")

        answers = []
        with st.form("onboarding_form"):
            for item in QUESTIONS:
                labels = [o[0] for o in item["options"]]
                choice = st.radio(item["q"], labels, key=item["q"])
                score = dict(item["options"])[choice]
                answers.append(score)
            submitted = st.form_submit_button("Save my risk profile", use_container_width=True)

        if submitted:
            total, risk_profile = compute_risk_profile(answers)
            try:
                client = get_authed_client(get_access_token())
                client.table("profiles").update({
                    "risk_score": total,
                    "risk_profile": risk_profile,
                    "onboarding_complete": True,
                }).eq("id", get_user_id()).execute()
                refresh_profile()
                st.success(f"Profile set: **{risk_profile.capitalize()}** (score {total}/15)")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save profile: {e}")


# ---------------------------------------------------------------------------
# Main routing
# ---------------------------------------------------------------------------

def main():
    if "session" not in st.session_state:
        render_auth()
        return

    profile = get_profile()
    onboarded = profile.get("onboarding_complete", False)

    if not onboarded:
        render_sidebar()
        render_onboarding()
        return

    render_sidebar()
    # Default landing: redirect to Dashboard
    st.switch_page("pages/1_Dashboard.py")


if __name__ == "__main__":
    main()
