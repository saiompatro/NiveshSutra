"""Settings page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from auth import (
    get_access_token,
    get_profile,
    get_user_id,
    logout,
    refresh_profile,
    require_auth,
)
from design import (
    apply_theme,
    render_empty_state,
    render_info_band,
    render_note_card,
    render_page_hero,
    render_section_heading,
    render_sidebar_shell,
)
from supabase_client import get_authed_client
from utils import RISK_QUESTIONS, compute_risk_profile

st.set_page_config(page_title="Settings | NiveshSutra", layout="wide")
apply_theme()
require_auth()


def _render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page="Settings",
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
        headline="Calibrate the profile, notification posture, and preferences that shape how the rest of the product behaves.",
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.switch_page("app.py")


_render_sidebar()
token = get_access_token()
user_id = get_user_id()
profile = get_profile()

render_page_hero(
    kicker="Settings",
    title="Account & preferences",
    body=f"Risk profile: {(profile.get('risk_profile') or 'Unassigned').capitalize()} | "
         f"Score: {profile.get('risk_score', 'n/a')}/15",
    pills=[],
)

tab_profile, tab_risk, tab_notifications = st.tabs(["Profile", "Risk Assessment", "Notifications"])

with tab_profile:
    render_section_heading(
        "Identity and profile state",
        "Simple account details, staged with the same tone as the rest of the app.",
        kicker="Profile",
    )
    info_left, info_right = st.columns([0.95, 1.05], gap="large")
    with info_left:
        render_note_card(
            "Current profile",
            "A concise read on how the app currently classifies your investing posture.",
            rows=[
                ("Email", st.session_state["user"].email),
                ("Risk profile", (profile.get("risk_profile") or "Unassigned").capitalize()),
                ("Risk score", f"{profile.get('risk_score', 'n/a')}/15"),
            ],
        )
    with info_right:
        with st.form("profile_form"):
            full_name = st.text_input("Full name", value=profile.get("full_name") or "")
            save = st.form_submit_button("Save changes", use_container_width=True)
        if save:
            try:
                get_authed_client(token).table("profiles").update({"full_name": full_name}).eq(
                    "id", user_id
                ).execute()
                refresh_profile()
                st.success("Profile updated.")
            except Exception as exc:
                st.error(f"Failed: {exc}")

with tab_risk:
    render_section_heading(
        "Retake your risk questionnaire",
        "This is the same five-question calibration flow used during onboarding, now restaged as a control deck.",
        kicker="Risk engine",
    )
    risk_cols = st.columns(3, gap="large")
    with risk_cols[0]:
        render_note_card("Conservative", "Prioritizes higher-confidence signals and smaller sizing guidance.")
    with risk_cols[1]:
        render_note_card("Moderate", "Balances confidence, breadth, and optionality in the signal list.")
    with risk_cols[2]:
        render_note_card("Aggressive", "Surfaces directional ideas earlier and supports larger sizing hints.")

    answers = []
    with st.form("risk_form"):
        for item in RISK_QUESTIONS:
            labels = [option[0] for option in item["options"]]
            choice = st.radio(item["q"], labels, key=f"risk_{item['q']}")
            answers.append(dict(item["options"])[choice])
        submitted = st.form_submit_button("Update risk profile", use_container_width=True)

    if submitted:
        total, new_profile = compute_risk_profile(answers)
        try:
            get_authed_client(token).table("profiles").update(
                {
                    "risk_score": total,
                    "risk_profile": new_profile,
                    "onboarding_complete": True,
                }
            ).eq("id", user_id).execute()
            refresh_profile()
            st.success(f"Risk profile updated to {new_profile.capitalize()} with a score of {total}/15.")
        except Exception as exc:
            st.error(f"Failed: {exc}")

with tab_notifications:
    render_section_heading(
        "Notification posture",
        "Alerting is treated like a first-class part of the product, because tracked signals are part of the core loop.",
        kicker="Notifications",
    )
    email_enabled = profile.get("email_notifications_enabled", True)
    toggled = st.toggle("Enable email notifications", value=email_enabled)
    if toggled != email_enabled:
        try:
            get_authed_client(token).table("profiles").update(
                {"email_notifications_enabled": toggled}
            ).eq("id", user_id).execute()
            refresh_profile()
            status = "enabled" if toggled else "disabled"
            st.success(f"Email notifications {status}.")
        except Exception as exc:
            st.error(f"Failed: {exc}")

    st.markdown("")
    try:
        tracked = (
            get_authed_client(token)
            .table("signal_notifications")
            .select("id, symbol, last_signal, is_active, created_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
        if tracked:
            for item in tracked:
                row = st.columns([1.3, 1.6, 1], gap="small")
                row[0].markdown(f"**{item['symbol']}**")
                row[1].markdown(item.get("last_signal", "-").replace("_", " ").title())
                with row[2]:
                    if st.button("Stop tracking", key=f"stop_tracking_{item['id']}", use_container_width=True):
                        get_authed_client(token).table("signal_notifications").update(
                            {"is_active": False}
                        ).eq("id", item["id"]).eq("user_id", user_id).execute()
                        st.rerun()
                st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)
        else:
            render_empty_state("No tracked signals yet", "Accept a signal on the Signals page to create your first notification workflow.")
    except Exception as exc:
        st.error(f"Could not load tracked signals: {exc}")
