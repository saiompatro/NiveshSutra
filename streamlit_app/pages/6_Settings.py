"""Settings — profile update, risk re-assessment, notification preferences."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from auth import require_auth, get_access_token, get_user_id, get_profile, refresh_profile
from supabase_client import get_authed_client
from utils import compute_risk_profile

st.set_page_config(page_title="Settings — NiveshSutra", page_icon="⚙️", layout="wide")
require_auth()

token = get_access_token()
uid = get_user_id()
profile = get_profile()

st.title("⚙️ Settings")

tab_profile, tab_risk, tab_notif = st.tabs(["Profile", "Risk Assessment", "Notifications"])

# ---------------------------------------------------------------------------
# Profile tab
# ---------------------------------------------------------------------------

with tab_profile:
    st.subheader("Profile")
    st.markdown(f"**Email:** {st.session_state['user'].email}")
    st.markdown(f"**Risk Profile:** {profile.get('risk_profile', '—').capitalize()}")
    st.markdown(f"**Risk Score:** {profile.get('risk_score', '—')}/15")

    st.divider()
    st.markdown("**Update display name**")
    with st.form("profile_form"):
        full_name = st.text_input("Full name", value=profile.get("full_name") or "")
        save = st.form_submit_button("Save changes")
    if save:
        try:
            get_authed_client(token).table("profiles").update(
                {"full_name": full_name}
            ).eq("id", uid).execute()
            refresh_profile()
            st.success("Profile updated.")
        except Exception as e:
            st.error(f"Failed: {e}")

# ---------------------------------------------------------------------------
# Risk Re-assessment tab
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

with tab_risk:
    st.subheader("Risk Re-assessment")
    st.caption(
        "Retake the questionnaire to update your risk profile. "
        "This affects signal personalisation and portfolio optimisation."
    )
    current = profile.get("risk_profile", "—")
    st.info(f"Current profile: **{current.capitalize()}**")

    answers = []
    with st.form("risk_form"):
        for item in QUESTIONS:
            labels = [o[0] for o in item["options"]]
            # Default to current answer if available
            choice = st.radio(item["q"], labels, key=f"set_risk_{item['q']}")
            score = dict(item["options"])[choice]
            answers.append(score)
        submitted = st.form_submit_button("Update risk profile")

    if submitted:
        total, new_profile = compute_risk_profile(answers)
        try:
            get_authed_client(token).table("profiles").update({
                "risk_score": total,
                "risk_profile": new_profile,
                "onboarding_complete": True,
            }).eq("id", uid).execute()
            refresh_profile()
            st.success(
                f"Risk profile updated to **{new_profile.capitalize()}** (score {total}/15). "
                "Signals page will reflect this on next load."
            )
        except Exception as e:
            st.error(f"Failed: {e}")

# ---------------------------------------------------------------------------
# Notifications tab
# ---------------------------------------------------------------------------

with tab_notif:
    st.subheader("Email Notifications")
    st.caption("Control whether you receive email alerts for signal changes.")

    email_enabled = profile.get("email_notifications_enabled", True)
    new_val = st.toggle("Enable email notifications", value=email_enabled)

    if new_val != email_enabled:
        try:
            get_authed_client(token).table("profiles").update(
                {"email_notifications_enabled": new_val}
            ).eq("id", uid).execute()
            refresh_profile()
            status = "enabled" if new_val else "disabled"
            st.success(f"Email notifications {status}.")
        except Exception as e:
            st.error(f"Failed: {e}")

    st.divider()
    st.markdown("**Tracked Signal Notifications**")

    try:
        tracked = (
            get_authed_client(token)
            .table("signal_notifications")
            .select("id, symbol, last_signal, is_active, created_at")
            .eq("user_id", uid)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
            .data or []
        )
        if tracked:
            for t in tracked:
                tc1, tc2, tc3 = st.columns([3, 3, 2])
                tc1.markdown(f"**{t['symbol']}**")
                tc2.markdown(t.get("last_signal", "—").replace("_", " ").title())
                if tc3.button("Stop tracking", key=f"settings_stop_{t['id']}"):
                    get_authed_client(token).table("signal_notifications").update(
                        {"is_active": False}
                    ).eq("id", t["id"]).eq("user_id", uid).execute()
                    st.rerun()
                st.markdown("<hr style='margin:3px 0;border-color:#1e293b'>", unsafe_allow_html=True)
        else:
            st.info("No signals tracked yet. Accept signals on the Signals page.")
    except Exception as e:
        st.error(f"Could not load tracked signals: {e}")
