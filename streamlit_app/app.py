"""NiveshSutra Streamlit entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from auth import (
    get_access_token,
    get_profile,
    get_user_id,
    login,
    logout,
    refresh_profile,
    signup,
)
from design import (
    apply_theme,
    render_info_band,
    render_metric_grid,
    render_note_card,
    render_page_hero,
    render_section_heading,
    render_sidebar_shell,
)
from supabase_client import get_authed_client
from utils import RISK_QUESTIONS, compute_risk_profile

st.set_page_config(
    page_title="NiveshSutra",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


def render_sidebar() -> None:
    """Render the shared authenticated sidebar."""
    profile = get_profile()
    render_sidebar_shell(
        active_page=None,
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
        headline="A premium control room for signals, portfolio motion, and market tempo.",
        show_nav=False,
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.rerun()


def render_auth() -> None:
    """Render the unauthenticated landing and auth flows."""
    hero_col, form_col = st.columns([1.35, 0.95], gap="large")

    with hero_col:
        render_page_hero(
            kicker="Signal atelier",
            title="Read the pulse of Indian equities like a crafted editorial.",
            body=(
                "NiveshSutra turns raw market data, sentiment, and portfolio math into a cinematic "
                "operating surface. Track conviction, shape risk, and move from noise to action."
            ),
            pills=[
                "Live NSE universe",
                "FinBERT news sentiment",
                "Signal + optimizer workflow",
            ],
            aside_title="Inside the experience",
            aside_rows=[
                ("Atmosphere", "Editorial trading floor"),
                ("Core loop", "Scan, accept, rebalance"),
                ("Built for", "Indian equity investors"),
            ],
        )

        render_metric_grid(
            [
                {
                    "label": "Universe",
                    "value": "Nifty + beyond",
                    "detail": "Explore benchmark names and onboard additional NSE symbols on demand.",
                    "tone": "emerald",
                },
                {
                    "label": "Decision layer",
                    "value": "Signals with context",
                    "detail": "Technical momentum, sentiment flow, and risk-aware conviction in one place.",
                    "tone": "amber",
                },
                {
                    "label": "Portfolio motion",
                    "value": "Rebalance intelligently",
                    "detail": "Translate holdings into weight, drift, and optimization actions without leaving the app.",
                    "tone": "rose",
                },
            ]
        )

    with form_col:
        render_section_heading(
            "Enter the studio",
            "Create an account or return to your workspace. The app keeps the operational flows native to Streamlit while giving the interface a stronger brand presence.",
            kicker="Access",
        )

        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@domain.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Open workspace", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Fill in both fields before continuing.")
                else:
                    with st.spinner("Opening your workspace..."):
                        ok, err = login(email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(f"Login failed: {err}")

        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email", placeholder="you@domain.com")
                new_pass = st.text_input("Password", type="password", key="signup_password")
                confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
                submitted_signup = st.form_submit_button("Create account", use_container_width=True)
            if submitted_signup:
                if not new_email or not new_pass:
                    st.error("Fill in all fields before creating your account.")
                elif new_pass != confirm:
                    st.error("Passwords do not match.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating your account..."):
                        ok, message = signup(new_email, new_pass)
                    if ok and message == "CHECK_EMAIL":
                        st.success("Account created. Confirm your email, then return here to log in.")
                    elif ok:
                        st.rerun()
                    else:
                        st.error(f"Signup failed: {message}")

        render_info_band(
            "What changes after login",
            "Your risk questionnaire shapes signal ranking, confidence thresholds, and portfolio recommendations across the entire product.",
        )

    st.markdown("")
    render_section_heading(
        "Why the redesign works in Streamlit",
        "The new direction leans on custom CSS, native page routing, Plotly theming, and interactive forms that Streamlit handles reliably. That keeps the look expressive without compromising maintainability.",
        kicker="Implementation logic",
    )
    story_cols = st.columns(3, gap="large")
    with story_cols[0]:
        render_note_card(
            "Poster-like first impression",
            "The landing screen behaves like a brand poster first and a form second, with a strong visual hierarchy and tight copy.",
            rows=[
                ("Headline", "Editorial serif scale"),
                ("Mood", "Copper + emerald over midnight"),
            ],
        )
    with story_cols[1]:
        render_note_card(
            "Navigation with intent",
            "Default multipage chrome is replaced by a custom sidebar shell so every page feels connected to the same product system.",
            rows=[
                ("Routing", "Native page links"),
                ("State", "Session-aware sidebar"),
            ],
        )
    with story_cols[2]:
        render_note_card(
            "Data views that still feel premium",
            "Dense market information is presented through themed metric cards, panel blocks, and charts instead of a generic dashboard grid.",
            rows=[
                ("Charts", "Shared Plotly skin"),
                ("Controls", "Styled native widgets"),
            ],
        )


def render_onboarding() -> None:
    """Render the risk questionnaire."""
    render_page_hero(
        kicker="Calibration",
        title="Shape the tone of your portfolio engine.",
        body=(
            "Answer five quick questions so NiveshSutra can tune signal ordering, confidence cutoffs, "
            "and allocation guidance to your investment posture."
        ),
        pills=["5 prompts", "Immediate personalization", "Used across signals and optimizer"],
        aside_title="What gets tuned",
        aside_rows=[
            ("Signals", "Ranking and confidence filters"),
            ("Portfolio", "Optimizer recommendations"),
            ("Alerts", "Sharper relevance"),
        ],
    )

    info_cols = st.columns(3, gap="large")
    with info_cols[0]:
        render_note_card(
            "Conservative",
            "Higher-confidence ideas surface first, with smaller suggested position sizes and less noise.",
        )
    with info_cols[1]:
        render_note_card(
            "Moderate",
            "Balanced ranking between conviction and optionality, designed for steady decision-making.",
        )
    with info_cols[2]:
        render_note_card(
            "Aggressive",
            "Directional opportunities show up earlier, with broader signal coverage and larger sizing hints.",
        )

    with st.form("onboarding_form"):
        answers = []
        for item in RISK_QUESTIONS:
            labels = [option[0] for option in item["options"]]
            choice = st.radio(item["q"], labels, key=item["q"])
            answers.append(dict(item["options"])[choice])
        submitted = st.form_submit_button("Save my risk profile", use_container_width=True)

    if submitted:
        total, risk_profile = compute_risk_profile(answers)
        try:
            client = get_authed_client(get_access_token())
            client.table("profiles").update(
                {
                    "risk_score": total,
                    "risk_profile": risk_profile,
                    "onboarding_complete": True,
                }
            ).eq("id", get_user_id()).execute()
            refresh_profile()
            st.success(f"Profile set to {risk_profile.capitalize()} with a score of {total}/15.")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save profile: {exc}")


def main() -> None:
    if "session" not in st.session_state:
        render_auth()
        return

    profile = get_profile()
    onboarded = profile.get("onboarding_complete", False)
    render_sidebar()

    if not onboarded:
        render_onboarding()
        return

    st.switch_page("pages/1_Dashboard.py")


if __name__ == "__main__":
    main()
