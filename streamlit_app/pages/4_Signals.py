"""Signals page."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from auth import get_access_token, get_profile, get_user_id, logout, require_auth
from design import (
    apply_theme,
    render_empty_state,
    render_info_band,
    render_metric_grid,
    render_note_card,
    render_page_hero,
    render_section_heading,
    render_sidebar_shell,
)
from supabase_client import get_anon_client, get_authed_client
from utils import (
    format_signal,
    get_confidence_threshold,
    get_position_size_hint,
    personalize_signals,
    signal_badge_html,
)

st.set_page_config(page_title="Signals | NiveshSutra", layout="wide")
apply_theme()
require_auth()


def _render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page="Signals",
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
        headline="The conviction engine: ranked ideas, sizing hints, and tracked signal changes in one theatrical lane.",
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.switch_page("app.py")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_signals() -> list[dict]:
    rows = (
        get_anon_client()
        .table("signals")
        .select("symbol, signal, confidence, technical_score, sentiment_score, momentum_score, created_at, date")
        .order("date", desc=True)
        .limit(200)
        .execute()
        .data
        or []
    )
    seen = set()
    latest = []
    for row in rows:
        if row["symbol"] not in seen:
            seen.add(row["symbol"])
            latest.append(row)
    return latest


@st.cache_data(ttl=60, show_spinner=False)
def fetch_accepted_signals(user_id: str, access_token: str) -> list[dict]:
    try:
        return (
            get_authed_client(access_token)
            .table("signal_notifications")
            .select("id, symbol, last_signal, last_notified_at, is_active, created_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def accept_signal(
    symbol: str,
    signal_type: str,
    composite_score: float,
    signal_date: str,
    user_id: str,
    access_token: str,
) -> None:
    get_authed_client(access_token).table("signal_notifications").upsert(
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


def stop_tracking(notification_id: str, user_id: str, access_token: str) -> None:
    get_authed_client(access_token).table("signal_notifications").update({"is_active": False}).eq(
        "id", notification_id
    ).eq("user_id", user_id).execute()


def render_signal_row(
    signal_row: dict,
    *,
    accepted_symbols: set[str],
    user_id: str,
    access_token: str,
    confidence_threshold: float,
    dimmed: bool = False,
    risk_profile: str,
) -> None:
    opacity = "0.55" if dimmed else "1"
    row = st.columns([1.2, 1.4, 1, 1, 1, 1, 2.1, 1], gap="small")
    confidence = (signal_row.get("confidence") or 0) * 100
    row[0].markdown(
        f"<span style='opacity:{opacity};font-weight:700'>{signal_row['symbol']}</span>",
        unsafe_allow_html=True,
    )
    row[1].markdown(
        f"<span style='opacity:{opacity}'>{signal_badge_html(signal_row['signal'])}</span>",
        unsafe_allow_html=True,
    )
    row[2].markdown(
        f"<span style='opacity:{opacity}'>{confidence:.0f}%</span>",
        unsafe_allow_html=True,
    )
    row[3].markdown(
        f"<span style='opacity:{opacity}'>{(signal_row.get('technical_score') or 0) * 100:.0f}%</span>",
        unsafe_allow_html=True,
    )
    row[4].markdown(
        f"<span style='opacity:{opacity}'>{(signal_row.get('sentiment_score') or 0) * 100:.0f}%</span>",
        unsafe_allow_html=True,
    )
    row[5].markdown(
        f"<span style='opacity:{opacity}'>{(signal_row.get('momentum_score') or 0) * 100:.0f}%</span>",
        unsafe_allow_html=True,
    )
    row[6].markdown(
        f"<span style='opacity:{opacity};color:#6c757d'>{get_position_size_hint(risk_profile, signal_row['signal']) or 'Observe only'}</span>",
        unsafe_allow_html=True,
    )

    if signal_row["symbol"] in accepted_symbols:
        row[7].markdown("<span style='color:#343a40'>Tracked</span>", unsafe_allow_html=True)
    else:
        if row[7].button("Accept", key=f"accept_{signal_row['symbol']}", use_container_width=True):
            st.session_state[f"accept_dialog_{signal_row['symbol']}"] = True
            st.session_state["accept_signal_data"] = signal_row
            st.rerun()

    if st.session_state.get(f"accept_dialog_{signal_row['symbol']}"):
        with st.form(f"accept_form_{signal_row['symbol']}"):
            render_section_heading(
                f"Accept {signal_row['symbol']}",
                "Track the signal and optionally convert buy-side conviction into a holding.",
                kicker="Action",
            )
            st.markdown(
                f"{signal_badge_html(signal_row['signal'])} "
                f"<span style='color:#6c757d;font-size:0.85rem'>Confidence {confidence:.0f}%</span>",
                unsafe_allow_html=True,
            )
            quantity = None
            price_input = None
            if signal_row["signal"] in {"buy", "strong_buy"}:
                qty_col, price_col = st.columns(2, gap="medium")
                quantity = qty_col.number_input(
                    "Quantity",
                    min_value=0,
                    step=1,
                    key=f"qty_{signal_row['symbol']}",
                )
                price_input = price_col.number_input(
                    "Buy price",
                    min_value=0.0,
                    step=0.01,
                    key=f"price_{signal_row['symbol']}",
                )
            submit_col, cancel_col = st.columns(2, gap="medium")
            confirmed = submit_col.form_submit_button("Track signal", use_container_width=True)
            cancelled = cancel_col.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.pop(f"accept_dialog_{signal_row['symbol']}", None)
            st.rerun()
        if confirmed:
            try:
                accept_signal(
                    signal_row["symbol"],
                    signal_row["signal"],
                    signal_row.get("confidence", 0) or 0,
                    signal_row.get("date") or signal_row.get("created_at", ""),
                    user_id,
                    access_token,
                )
                if signal_row["signal"] in {"buy", "strong_buy"} and quantity and price_input:
                    get_authed_client(access_token).table("holdings").insert(
                        {
                            "user_id": user_id,
                            "symbol": signal_row["symbol"],
                            "quantity": quantity,
                            "avg_buy_price": price_input,
                        }
                    ).execute()
                fetch_accepted_signals.clear()
                st.success(f"Signal for {signal_row['symbol']} accepted.")
                st.session_state.pop(f"accept_dialog_{signal_row['symbol']}", None)
                st.rerun()
            except Exception as exc:
                st.error(f"Failed: {exc}")

    st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)


_render_sidebar()
token = get_access_token()
user_id = get_user_id()
profile = get_profile()
risk_profile = profile.get("risk_profile", "moderate")

with st.spinner("Loading signals..."):
    all_signals = fetch_signals()
    accepted = fetch_accepted_signals(user_id, token)

accepted_symbols = {item["symbol"] for item in accepted}
confidence_threshold = get_confidence_threshold(risk_profile)

render_page_hero(
    kicker="Signals",
    title="Conviction engine",
    body=f"Profile: {risk_profile.capitalize()} · "
         f"Threshold: {confidence_threshold * 100:.0f}%+ confidence · "
         f"{len(accepted)} tracked",
    pills=[],
)

counts: dict[str, int] = {}
for signal_row in all_signals:
    counts[signal_row["signal"]] = counts.get(signal_row["signal"], 0) + 1

render_metric_grid(
    [
        {
            "label": "Strong buy",
            "value": str(counts.get("strong_buy", 0)),
            "detail": "Top-end bullish conviction in the current signal set.",
            "tone": "emerald",
        },
        {
            "label": "Buy",
            "value": str(counts.get("buy", 0)),
            "detail": "Positive directional calls that can still graduate into tracked positions.",
            "tone": "emerald",
        },
        {
            "label": "Hold",
            "value": str(counts.get("hold", 0)),
            "detail": "Names that currently read as neutral.",
            "tone": "amber",
        },
        {
            "label": "Sell side",
            "value": str(counts.get("sell", 0) + counts.get("strong_sell", 0)),
            "detail": "Bearish names or exit-oriented calls across the active universe.",
            "tone": "rose",
        },
    ],
    columns=4,
)

render_info_band(
    "Ranking logic",
    f"Signals above {confidence_threshold * 100:.0f}% confidence for your {risk_profile} profile are staged first. Lower-confidence names remain visible, but intentionally dimmed to keep the eye on the main action.",
)

filter_col, rail_col = st.columns([1.4, 0.9], gap="large")
with filter_col:
    signal_filter = st.selectbox(
        "Filter by signal",
        ["all", "strong_buy", "buy", "hold", "sell", "strong_sell"],
        format_func=lambda value: "All signals" if value == "all" else format_signal(value),
    )

filtered = [row for row in all_signals if signal_filter == "all" or row["signal"] == signal_filter]
filtered = personalize_signals(filtered, risk_profile)
recommended = [
    row
    for row in filtered
    if (row.get("confidence") or 0) >= confidence_threshold and row["signal"] != "hold"
]
other = [row for row in filtered if row not in recommended]

with rail_col:
    render_note_card(
        "Signal summary",
        f"Signals at or above {confidence_threshold * 100:.0f}% confidence for your {risk_profile.capitalize()} profile are shown first.",
        rows=[
            ("Recommended", str(len(recommended))),
            ("Other visible", str(len(other))),
            ("Tracked", str(len(accepted))),
        ],
    )

render_section_heading(
    "Recommended first",
    "High-confidence names aligned with your posture appear at the top, ready to be tracked or turned into holdings.",
    kicker="Main lane",
)

header = st.columns([1.2, 1.4, 1, 1, 1, 1, 2.1, 1], gap="small")
for column, label in zip(
    header,
    ["Symbol", "Signal", "Confidence", "Technical", "Sentiment", "Momentum", "Sizing note", "Action"],
    strict=False,
):
    column.markdown(f"**{label}**")
st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)

if recommended:
    for signal_row in recommended:
        render_signal_row(
            signal_row,
            accepted_symbols=accepted_symbols,
            user_id=user_id,
            access_token=token,
            confidence_threshold=confidence_threshold,
            risk_profile=risk_profile,
        )
else:
    render_empty_state("No signals meet the current threshold", "Lower-confidence names may still appear below, or the signal filter may be too narrow.")

if other:
    render_section_heading(
        "Lower-priority ideas",
        "Still visible for context, but visually quieter so the page retains a clear focal point.",
        kicker="Supporting lane",
    )
    for signal_row in other:
        render_signal_row(
            signal_row,
            accepted_symbols=accepted_symbols,
            user_id=user_id,
            access_token=token,
            confidence_threshold=confidence_threshold,
            dimmed=bool(recommended),
            risk_profile=risk_profile,
        )

if accepted:
    render_section_heading(
        "Tracked signals",
        "These names stay in your notification loop until you stop following them.",
        kicker="Monitoring",
    )
    for item in accepted:
        row = st.columns([1.2, 1.4, 1.6, 1], gap="small")
        row[0].markdown(f"**{item['symbol']}**")
        row[1].markdown(signal_badge_html(item.get("last_signal", "")), unsafe_allow_html=True)
        timestamp = item.get("last_notified_at", item.get("created_at", ""))
        try:
            pretty_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%d %b %Y")
        except Exception:
            pretty_date = timestamp or "Unknown"
        row[2].markdown(f"<span style='color:#6c757d'>{pretty_date}</span>", unsafe_allow_html=True)
        with row[3]:
            if st.button("Stop", key=f"stop_{item['id']}", use_container_width=True):
                stop_tracking(item["id"], user_id, token)
                fetch_accepted_signals.clear()
                st.rerun()
        st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)
else:
    render_note_card(
        "No tracked signals yet",
        "Accept any buy, strong buy, sell, or strong sell call above to create your first monitored lane.",
    )
