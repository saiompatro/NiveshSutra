"""Signals — AI trading signals with risk-profile personalization."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from auth import require_auth, get_access_token, get_user_id, get_profile
from supabase_client import get_anon_client, get_authed_client
from utils import (
    signal_badge_html, format_signal, signal_color,
    personalize_signals, get_confidence_threshold, get_position_size_hint,
)

st.set_page_config(page_title="Signals — NiveshSutra", page_icon="⚡", layout="wide")
require_auth()

token = get_access_token()
uid = get_user_id()
profile = get_profile()
risk_profile = profile.get("risk_profile", "moderate")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_signals() -> list:
    rows = (
        get_anon_client()
        .table("signals")
        .select("symbol, signal, confidence, technical_score, sentiment_score, momentum_score, created_at, date")
        .order("date", desc=True)
        .limit(200)
        .execute()
        .data or []
    )
    seen, latest = set(), []
    for r in rows:
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            latest.append(r)
    return latest


@st.cache_data(ttl=60, show_spinner=False)
def fetch_accepted_signals(user_id: str, access_token: str) -> list:
    try:
        return (
            get_authed_client(access_token)
            .table("signal_notifications")
            .select("id, symbol, last_signal, last_notified_at, is_active, created_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
            .data or []
        )
    except Exception:
        return []


def accept_signal(symbol: str, signal_type: str, composite_score: float,
                  signal_date: str, user_id: str, access_token: str):
    client = get_authed_client(access_token)
    client.table("signal_notifications").upsert(
        {
            "user_id": user_id,
            "symbol": symbol,
            "last_signal": signal_type,
            "composite_score": composite_score,
            "signal_date": signal_date,
            "is_active": True,
        },
        on_conflict="user_id,symbol",
    ).execute()


def stop_tracking(notification_id: str, user_id: str, access_token: str):
    get_authed_client(access_token).table("signal_notifications").update(
        {"is_active": False}
    ).eq("id", notification_id).eq("user_id", user_id).execute()


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

st.title("⚡ Signals")
st.caption("AI-generated trading signals personalised for your risk profile")

with st.spinner("Loading signals…"):
    all_signals = fetch_signals()
    accepted = fetch_accepted_signals(uid, token)

accepted_symbols = {a["symbol"] for a in accepted}
confidence_threshold = get_confidence_threshold(risk_profile)

# Risk profile banner
risk_color = {"conservative": "#22c55e", "moderate": "#3b82f6", "aggressive": "#f97316"}.get(
    risk_profile, "#94a3b8"
)
risk_desc = {
    "conservative": "Higher-confidence signals shown first. Aggressive calls are de-prioritised.",
    "moderate": "Balanced signal view with standard confidence thresholds.",
    "aggressive": "All signals shown. Strong directional signals are prioritised.",
}.get(risk_profile, "")
st.markdown(
    f"<div style='background:#1e293b;border:1px solid {risk_color}30;border-radius:8px;"
    f"padding:10px 16px;margin-bottom:16px;display:flex;align-items:center;gap:12px'>"
    f"<span style='font-size:1.3rem'>🛡️</span>"
    f"<div><strong style='color:{risk_color}'>Personalised for {risk_profile.capitalize()} profile</strong>"
    f"<br><span style='font-size:0.8rem;color:#94a3b8'>{risk_desc}</span></div></div>",
    unsafe_allow_html=True,
)

# Summary counts
counts: dict[str, int] = {}
for s in all_signals:
    counts[s["signal"]] = counts.get(s["signal"], 0) + 1

sc1, sc2, sc3, sc4, sc5 = st.columns(5)
for col, key, label, color in [
    (sc1, "strong_buy",  "Strong Buy",  "#22c55e"),
    (sc2, "buy",         "Buy",         "#10b981"),
    (sc3, "hold",        "Hold",        "#eab308"),
    (sc4, "sell",        "Sell",        "#f97316"),
    (sc5, "strong_sell", "Strong Sell", "#ef4444"),
]:
    col.markdown(
        f"<div style='background:#1e293b;border-radius:8px;padding:12px;text-align:center'>"
        f"<p style='margin:0;font-size:0.75rem;color:#94a3b8'>{label}</p>"
        f"<p style='margin:0;font-size:1.8rem;font-weight:700;color:{color}'>"
        f"{counts.get(key, 0)}</p></div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Filter + sort
filter_col, _ = st.columns([2, 4])
with filter_col:
    SIGNAL_TYPES = ["all", "strong_buy", "buy", "hold", "sell", "strong_sell"]
    sig_filter = st.selectbox(
        "Filter by signal",
        SIGNAL_TYPES,
        format_func=lambda x: "All Signals" if x == "all" else format_signal(x),
    )

filtered = [s for s in all_signals if sig_filter == "all" or s["signal"] == sig_filter]
filtered = personalize_signals(filtered, risk_profile)

recommended = [
    s for s in filtered
    if (s.get("confidence") or 0) >= confidence_threshold and s["signal"] != "hold"
]
other = [s for s in filtered if s not in recommended]

# Table helper
def render_signal_row(s: dict, dimmed: bool = False):
    row = st.columns([2, 2, 2, 2, 2, 2, 3, 2])
    opacity = "0.5" if dimmed else "1"

    # Symbol
    row[0].markdown(
        f"<span style='opacity:{opacity};font-weight:600'>{s['symbol']}</span>",
        unsafe_allow_html=True,
    )
    # Signal badge
    row[1].markdown(
        f"<span style='opacity:{opacity}'>{signal_badge_html(s['signal'])}</span>",
        unsafe_allow_html=True,
    )
    # Confidence bar
    conf = (s.get("confidence") or 0) * 100
    row[2].markdown(
        f"<div style='opacity:{opacity}'>"
        f"<div style='background:#334155;border-radius:4px;height:6px;margin-top:8px'>"
        f"<div style='background:#3b82f6;width:{conf:.0f}%;height:6px;border-radius:4px'></div></div>"
        f"<span style='font-size:0.75rem;color:#94a3b8'>{conf:.0f}%</span></div>",
        unsafe_allow_html=True,
    )
    # Component scores
    for i, key in enumerate(["technical_score", "sentiment_score", "momentum_score"]):
        val = (s.get(key) or 0) * 100
        row[3 + i].markdown(
            f"<span style='opacity:{opacity};font-size:0.85rem'>{val:.0f}%</span>",
            unsafe_allow_html=True,
        )
    # Size hint
    hint = get_position_size_hint(risk_profile, s["signal"])
    row[6].markdown(
        f"<span style='opacity:{opacity};font-size:0.75rem;color:#94a3b8'>{hint or '—'}</span>",
        unsafe_allow_html=True,
    )
    # Action
    if s["symbol"] in accepted_symbols:
        row[7].markdown(
            "<span style='color:#22c55e;font-size:0.8rem'>✓ Tracked</span>",
            unsafe_allow_html=True,
        )
    else:
        if row[7].button("Accept", key=f"acc_{s['symbol']}"):
            st.session_state[f"accept_dialog_{s['symbol']}"] = True
            st.session_state["accept_signal_data"] = s
            st.rerun()

    # Accept dialog
    if st.session_state.get(f"accept_dialog_{s['symbol']}"):
        with st.form(f"accept_form_{s['symbol']}"):
            st.markdown(f"**Accept signal: {s['symbol']} — {format_signal(s['signal'])}**")
            st.caption(f"Confidence: {(s.get('confidence', 0) or 0) * 100:.0f}%")
            qty = price_input = None
            if s["signal"] in ("buy", "strong_buy"):
                st.markdown("Optionally add to portfolio:")
                q1, q2 = st.columns(2)
                qty = q1.number_input("Quantity", min_value=0, step=1, key=f"qty_{s['symbol']}")
                price_input = q2.number_input("Buy price (₹)", min_value=0.0, step=0.01, key=f"px_{s['symbol']}")
            btn_ok = st.form_submit_button("Accept Signal")
            btn_cancel = st.form_submit_button("Cancel")
        if btn_cancel:
            st.session_state.pop(f"accept_dialog_{s['symbol']}", None)
            st.rerun()
        if btn_ok:
            try:
                accept_signal(
                    s["symbol"], s["signal"],
                    s.get("confidence", 0) or 0,
                    s.get("date") or s.get("created_at", ""),
                    uid, token,
                )
                if s["signal"] in ("buy", "strong_buy") and qty and price_input:
                    get_authed_client(token).table("holdings").insert({
                        "user_id": uid,
                        "symbol": s["symbol"],
                        "quantity": qty,
                        "avg_buy_price": price_input,
                    }).execute()
                fetch_accepted_signals.clear()
                st.success(f"Signal for {s['symbol']} accepted!")
                st.session_state.pop(f"accept_dialog_{s['symbol']}", None)
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

    st.markdown("<hr style='margin:3px 0;border-color:#1e293b'>", unsafe_allow_html=True)


# Table headers
hdr = st.columns([2, 2, 2, 2, 2, 2, 3, 2])
for col, label in zip(hdr, ["Symbol", "Signal", "Confidence", "Technical", "Sentiment", "Momentum", "Suggested Size", "Action"]):
    col.markdown(f"**{label}**")
st.markdown("<hr style='margin:4px 0 6px;border-color:#334155'>", unsafe_allow_html=True)

if recommended:
    st.markdown(
        f"<p style='color:#3b82f6;font-size:0.82rem;margin:4px 0'>⭐ Recommended "
        f"(≥{confidence_threshold * 100:.0f}% confidence for {risk_profile})</p>",
        unsafe_allow_html=True,
    )
    for s in recommended:
        render_signal_row(s)

if recommended and other:
    st.markdown(
        "<p style='text-align:center;color:#475569;font-size:0.78rem;padding:6px'>"
        "ℹ Other signals (below confidence threshold)</p>",
        unsafe_allow_html=True,
    )

for s in other:
    render_signal_row(s, dimmed=bool(recommended))

if not recommended and not other:
    st.info("No signals found.")

# ---------------------------------------------------------------------------
# Tracked signals
# ---------------------------------------------------------------------------

if accepted:
    st.divider()
    st.subheader("✅ Tracked Signals")
    st.caption("You'll receive email alerts when these signals change")

    for a in accepted:
        ac1, ac2, ac3, ac4 = st.columns([2, 2, 3, 2])
        ac1.markdown(f"**{a['symbol']}**")
        sig_key = a.get("last_signal", "")
        ac2.markdown(signal_badge_html(sig_key), unsafe_allow_html=True)
        notified = a.get("last_notified_at", a.get("created_at", ""))
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(notified.replace("Z", "+00:00"))
            ac3.markdown(f"<span style='color:#94a3b8;font-size:0.8rem'>{dt.strftime('%d %b %Y')}</span>",
                         unsafe_allow_html=True)
        except Exception:
            ac3.markdown("")
        if ac4.button("Stop", key=f"stop_{a['id']}"):
            stop_tracking(a["id"], uid, token)
            fetch_accepted_signals.clear()
            st.rerun()
        st.markdown("<hr style='margin:3px 0;border-color:#1e293b'>", unsafe_allow_html=True)
