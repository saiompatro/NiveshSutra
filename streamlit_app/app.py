"""NiveshSutra — entry point: auth gate + onboarding wizard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import streamlit.components.v1 as components

from auth import (
    get_access_token,
    get_github_oauth_url,
    get_profile,
    get_user_id,
    handle_oauth_tokens,
    login,
    logout,
    refresh_profile,
    signup,
)
from config import get_setting
from design import apply_theme, render_sidebar_shell
from supabase_client import get_authed_client
from utils import RISK_QUESTIONS, compute_risk_profile

st.set_page_config(
    page_title="NiveshSutra",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


# ── OAuth hash-to-queryparams bridge ────────────────────────────────────────
# After GitHub OAuth, Supabase redirects back with tokens in the URL fragment.
# This small JS snippet extracts them and reloads with query params so Python
# can read them on the next render cycle.
components.html(
    """
    <script>
    (function () {
        var hash = window.location.hash;
        if (hash && hash.includes('access_token=')) {
            var params = new URLSearchParams(hash.substring(1));
            var at = params.get('access_token');
            var rt = params.get('refresh_token') || '';
            if (at) {
                var url = new URL(window.location.href);
                url.hash = '';
                url.searchParams.set('ns_at', at);
                url.searchParams.set('ns_rt', rt);
                window.location.replace(url.toString());
            }
        }
    })();
    </script>
    """,
    height=0,
)

# ── Handle OAuth callback ────────────────────────────────────────────────────
qp = st.query_params
if "ns_at" in qp and "session" not in st.session_state:
    ok, err = handle_oauth_tokens(qp["ns_at"], qp.get("ns_rt", ""))
    if ok:
        st.query_params.clear()
        st.rerun()
    else:
        st.error(f"GitHub sign-in failed: {err}")
        st.query_params.clear()


# ── Sidebar (authenticated) ──────────────────────────────────────────────────
def render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page=None,
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
        show_nav=False,
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.rerun()


# ── Login / sign-up page ─────────────────────────────────────────────────────
def render_auth() -> None:
    # Determine the app's public URL for OAuth redirect
    site_url = get_setting("SITE_URL", "http://localhost:8501")

    # Center the auth card
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        # Brand mark
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:1.75rem;margin-top:2rem">
                <div style="display:inline-flex;align-items:center;justify-content:center;
                            width:44px;height:44px;background:var(--accent);border-radius:12px;
                            font-weight:800;font-size:1.2rem;color:#fff;margin-bottom:0.75rem">
                    N
                </div>
                <div style="font-size:1.375rem;font-weight:700;color:var(--text);letter-spacing:-0.02em">
                    NiveshSutra
                </div>
                <div style="font-size:0.8125rem;color:var(--text-2);margin-top:0.25rem">
                    AI-powered Indian equity intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_signup = st.tabs(["Sign in", "Create account"])

        # ── Login ──
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign in", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Enter your email and password.")
                else:
                    with st.spinner("Signing in…"):
                        ok, err = login(email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(f"Sign-in failed: {err}")

        # ── Sign up ──
        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email", placeholder="you@example.com")
                new_pass = st.text_input("Password", type="password", key="signup_pw", placeholder="Min. 6 characters")
                confirm = st.text_input("Confirm password", type="password", key="signup_confirm", placeholder="••••••••")
                submitted_signup = st.form_submit_button("Create account", use_container_width=True)
            if submitted_signup:
                if not new_email or not new_pass:
                    st.error("Fill in all fields.")
                elif new_pass != confirm:
                    st.error("Passwords do not match.")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with st.spinner("Creating account…"):
                        ok, message = signup(new_email, new_pass)
                    if ok and message == "CHECK_EMAIL":
                        st.success("Check your email to confirm your account, then sign in.")
                    elif ok:
                        st.rerun()
                    else:
                        st.error(f"Sign-up failed: {message}")

        # ── GitHub OAuth ──
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:0.75rem;
                        margin:1rem 0;color:var(--muted);font-size:0.75rem">
                <div style="flex:1;height:1px;background:var(--border)"></div>
                or continue with
                <div style="flex:1;height:1px;background:var(--border)"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ok_gh, gh_url = get_github_oauth_url(site_url)
        if ok_gh:
            st.link_button(
                "⬡  GitHub",
                url=gh_url,
                use_container_width=True,
            )
        else:
            st.caption("GitHub sign-in unavailable — enable GitHub OAuth in your Supabase project.")


# ── Onboarding (risk questionnaire) ─────────────────────────────────────────
def render_onboarding() -> None:
    st.markdown(
        """
        <div class="ns-page-header">
            <h1>Set up your risk profile</h1>
            <p>Answer five quick questions so NiveshSutra can personalise signal ranking,
               confidence thresholds, and allocation guidance to your investing style.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    profile_cols = st.columns(3, gap="small")
    profiles = [
        ("Conservative", "Higher-confidence signals, smaller sizing guidance, lower noise."),
        ("Moderate", "Balanced conviction, breadth, and optionality across the signal list."),
        ("Aggressive", "Directional ideas surface earlier with broader coverage and larger size hints."),
    ]
    for col, (name, desc) in zip(profile_cols, profiles):
        with col:
            st.markdown(
                f"""
                <div class="ns-card" style="margin-bottom:0.75rem">
                    <h4>{name}</h4>
                    <div class="ns-card-body">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.form("onboarding_form"):
        answers = []
        for item in RISK_QUESTIONS:
            labels = [option[0] for option in item["options"]]
            choice = st.radio(item["q"], labels, key=item["q"])
            answers.append(dict(item["options"])[choice])
        submitted = st.form_submit_button("Save risk profile", use_container_width=True)

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
            st.success(f"Profile set to {risk_profile.capitalize()} (score {total}/15).")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save profile: {exc}")


# ── Main ─────────────────────────────────────────────────────────────────────
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
