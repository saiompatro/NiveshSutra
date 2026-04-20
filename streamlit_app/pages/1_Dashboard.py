"""Dashboard page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from api_client import request_json
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
from live_market import fetch_live_quote, fetch_live_quotes_batch
from supabase_client import get_anon_client, get_authed_client
from utils import format_currency, format_pct, signal_badge_html

st.set_page_config(page_title="Dashboard | NiveshSutra", layout="wide")
apply_theme()
require_auth()


def _render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page="Dashboard",
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.switch_page("app.py")


@st.cache_data(ttl=15, show_spinner=False)
def fetch_portfolio_performance(user_id: str, access_token: str) -> dict:
    try:
        holdings = request_json(
            "GET",
            "/api/v1/holdings/live",
            access_token=access_token,
        )
        if not holdings:
            return {}
        total_invested = 0.0
        current_value = 0.0
        for holding in holdings:
            invested = float(holding["quantity"]) * float(holding["avg_price"])
            value = float(holding["quantity"]) * float(holding["current_price"])
            total_invested += invested
            current_value += value
        pnl = current_value - total_invested
        pnl_pct = (pnl / total_invested * 100) if total_invested else 0.0
        return {
            "total_invested": total_invested,
            "total_value": current_value,
            "total_pnl": pnl,
            "total_pnl_pct": pnl_pct,
        }
    except Exception:
        try:
            client = get_authed_client(access_token)
            holdings = (
                client.table("holdings")
                .select("symbol, quantity, avg_buy_price, stocks(yf_ticker)")
                .eq("user_id", user_id)
                .execute()
                .data
                or []
            )
            if not holdings:
                return {}
            quote_map = fetch_live_quotes_batch(
                {
                    holding["symbol"]: (holding.get("stocks") or {}).get("yf_ticker")
                    for holding in holdings
                }
            )
            total_invested = 0.0
            current_value = 0.0
            for holding in holdings:
                quote = quote_map.get(holding["symbol"]) or {}
                invested = float(holding["quantity"]) * float(holding["avg_buy_price"])
                value = float(holding["quantity"]) * float(quote.get("price") or holding["avg_buy_price"])
                total_invested += invested
                current_value += value
            pnl = current_value - total_invested
            pnl_pct = (pnl / total_invested * 100) if total_invested else 0.0
            return {
                "total_invested": total_invested,
                "total_value": current_value,
                "total_pnl": pnl,
                "total_pnl_pct": pnl_pct,
            }
        except Exception:
            return {}


@st.cache_data(ttl=15, show_spinner=False)
def fetch_nifty50() -> dict:
    try:
        data = request_json("GET", "/api/v1/market/index-overview")
        if not data:
            return {}
        return {
            "value": float(data.get("nifty50_value") or 0),
            "change": float(data.get("nifty50_change") or 0),
            "change_pct": float(data.get("nifty50_change_pct") or 0),
            "provider": data.get("provider") or "",
        }
    except Exception:
        quote = fetch_live_quote("^NSEI")
        if not quote:
            return {}
        return {
            "value": float(quote.get("price") or 0),
            "change": float(quote.get("change") or 0),
            "change_pct": float(quote.get("change_pct") or 0),
            "provider": quote.get("provider") or "",
        }


@st.cache_data(ttl=120, show_spinner=False)
def fetch_market_sentiment() -> dict:
    try:
        result = (
            get_anon_client()
            .table("sentiment_daily")
            .select("symbol, avg_sentiment, date")
            .order("date", desc=True)
            .limit(50)
            .execute()
            .data
            or []
        )
        if not result:
            return {}
        latest_date = result[0]["date"]
        current_rows = [row for row in result if row["date"] == latest_date]
        scores = [float(row["avg_sentiment"]) for row in current_rows]
        average = sum(scores) / len(scores) if scores else 0.0
        bullish = sum(1 for score in scores if score > 0.1)
        bearish = sum(1 for score in scores if score < -0.1)
        neutral = len(scores) - bullish - bearish
        label = "Bullish" if average > 0.1 else ("Bearish" if average < -0.1 else "Neutral")
        return {
            "overall": label,
            "score": average,
            "bullish": bullish,
            "neutral": neutral,
            "bearish": bearish,
            "total": len(scores),
            "date": latest_date,
        }
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_latest_signals(limit: int = 5) -> list[dict]:
    try:
        rows = (
            get_anon_client()
            .table("signals")
            .select("symbol, signal, confidence, created_at")
            .order("created_at", desc=True)
            .limit(limit * 2)
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
            if len(latest) >= limit:
                break
        return latest
    except Exception:
        return []


@st.cache_data(ttl=15, show_spinner=False)
def fetch_watchlist_live(user_id: str, access_token: str) -> list[dict]:
    try:
        rows = request_json(
            "GET",
            "/api/v1/watchlist/live",
            access_token=access_token,
        )
        return [
            {
                "symbol": row["symbol"],
                "company_name": row.get("company_name", ""),
                "price": float(row.get("current_price") or 0),
                "change_pct": float(row.get("change_pct") or 0),
                "provider": row.get("provider") or "",
            }
            for row in rows[:8]
        ]
    except Exception:
        try:
            client = get_authed_client(access_token)
            rows = (
                client.table("watchlist")
                .select("symbol, stocks(company_name, yf_ticker)")
                .eq("user_id", user_id)
                .order("added_at", desc=True)
                .limit(8)
                .execute()
                .data
                or []
            )
            quote_map = fetch_live_quotes_batch(
                {
                    row["symbol"]: (row.get("stocks") or {}).get("yf_ticker")
                    for row in rows
                }
            )
            return [
                {
                    "symbol": row["symbol"],
                    "company_name": (row.get("stocks") or {}).get("company_name", ""),
                    "price": float((quote_map.get(row["symbol"]) or {}).get("price") or 0),
                    "change_pct": float((quote_map.get(row["symbol"]) or {}).get("change_pct") or 0),
                    "provider": (quote_map.get(row["symbol"]) or {}).get("provider") or "",
                }
                for row in rows
            ]
        except Exception:
            return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_alerts(user_id: str, access_token: str, limit: int = 5) -> list[dict]:
    try:
        client = get_authed_client(access_token)
        return (
            client.table("alerts")
            .select("id, title, message, is_read, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


_render_sidebar()
profile = get_profile()
token = get_access_token()
user_id = get_user_id()

with st.spinner("Loading dashboard..."):
    portfolio = fetch_portfolio_performance(user_id, token)
    nifty = fetch_nifty50()
    sentiment = fetch_market_sentiment()
    signals = fetch_latest_signals()
    watchlist = fetch_watchlist_live(user_id, token)
    alerts = fetch_alerts(user_id, token)

render_page_hero(
    kicker="Market panorama",
    title="Your investing control room.",
    body=(
        "Portfolio motion, market tone, fresh conviction, and watchlist heat all sit on one cinematic surface. "
        "Use it like a morning briefing, then dive deeper where the tape gets interesting."
    ),
    pills=[
        f"Risk profile: {(profile.get('risk_profile') or 'Unassigned').capitalize()}",
        f"Signals on deck: {len(signals)}",
        f"Watchlist names: {len(watchlist)}",
    ],
    aside_title="Current scene",
    aside_rows=[
        ("Portfolio", format_currency(portfolio.get("total_value", 0))),
        ("Nifty 50", f"{nifty.get('value', 0):,.2f}" if nifty else "Unavailable"),
        ("Mood", sentiment.get("overall", "Waiting on data") if sentiment else "Waiting on data"),
    ],
)

render_metric_grid(
    [
        {
            "label": "Portfolio value",
            "value": format_currency(portfolio.get("total_value", 0)),
            "detail": (
                f"PnL {format_pct(portfolio.get('total_pnl_pct', 0))} | "
                f"Invested {format_currency(portfolio.get('total_invested', 0))}"
            )
            if portfolio
            else "No holdings yet. Add positions in Portfolio to start the operating loop.",
            "tone": "emerald" if portfolio.get("total_pnl", 0) >= 0 else "rose",
        },
        {
            "label": "Index pulse",
            "value": f"{nifty.get('value', 0):,.2f}" if nifty else "No feed",
            "detail": (
                f"{format_pct(nifty.get('change_pct', 0))} today | "
                f"{nifty.get('change', 0):+.2f} points"
            )
            if nifty
            else "Market data is unavailable right now.",
            "tone": "amber",
        },
        {
            "label": "Sentiment regime",
            "value": sentiment.get("overall", "Neutral"),
            "detail": (
                f"Score {sentiment.get('score', 0):.3f} across {sentiment.get('total', 0)} names"
            )
            if sentiment
            else "Daily sentiment data has not landed yet.",
            "tone": "emerald" if sentiment.get("overall") == "Bullish" else "rose" if sentiment.get("overall") == "Bearish" else "amber",
        },
        {
            "label": "Alert load",
            "value": str(len(alerts)),
            "detail": "Unread changes, rebalance drift, and signal shifts collected in one lane.",
            "tone": "amber",
        },
    ],
    columns=4,
)

render_info_band(
    "Briefing note",
    "The redesigned dashboard avoids a wall of generic cards. Instead, it stages today’s operating signals first, then lets the supporting context sit in side lanes you can scan quickly.",
)

lead_col, story_col = st.columns([1.35, 0.9], gap="large")

with lead_col:
    render_section_heading(
        "Signal lane",
        "The latest conviction calls, surfaced without leaving the main dashboard.",
        kicker="Primary lane",
    )
    if signals:
        for signal in signals:
            row_left, row_mid, row_right = st.columns([1.3, 1.1, 0.9], gap="medium")
            row_left.markdown(
                f"**{signal['symbol']}**  \n"
                f"<span style='color:#9aabc4;font-size:0.82rem'>Confidence {signal.get('confidence', 0) * 100:.0f}%</span>",
                unsafe_allow_html=True,
            )
            row_mid.markdown(signal_badge_html(signal["signal"]), unsafe_allow_html=True)
            with row_right:
                if st.button("Open Signals", key=f"dash_signal_{signal['symbol']}", use_container_width=True):
                    st.switch_page("pages/4_Signals.py")
            st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)
    else:
        render_empty_state("No live signals yet", "Once the signal pipeline runs, your latest calls will appear here.")

    st.markdown("")
    render_section_heading(
        "Watchlist theater",
        "Quick movers in your personal radar.",
        kicker="Secondary lane",
    )
    if watchlist:
        for item in watchlist:
            change_pct = item["change_pct"]
            change_color = "#5de4c7" if change_pct >= 0 else "#ff7f90"
            row_left, row_mid, row_right = st.columns([1.4, 1, 0.9], gap="medium")
            row_left.markdown(
                f"**{item['symbol']}**  \n"
                f"<span style='color:#9aabc4;font-size:0.8rem'>{item['company_name']}</span>",
                unsafe_allow_html=True,
            )
            row_mid.markdown(
                f"<span style='font-size:1rem;color:#f7f2e9'>{item['price']:,.2f}</span>",
                unsafe_allow_html=True,
            )
            row_right.markdown(
                f"<span style='color:{change_color};font-weight:600'>{format_pct(change_pct)}</span>",
                unsafe_allow_html=True,
            )
            st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)
        if st.button("Browse Stocks", use_container_width=True, key="dash_open_stocks"):
            st.switch_page("pages/2_Stocks.py")
    else:
        render_empty_state("Watchlist is empty", "Add names from the Stocks page to start tracking live price changes here.")

with story_col:
    render_section_heading(
        "Context lanes",
        "Sentiment balance, operational alerts, and the way the redesign frames the story around the numbers.",
        kicker="Supporting detail",
    )
    render_note_card(
        "Market mood board",
        "Daily sentiment acts like a weather layer over the equity universe, showing whether headlines are adding lift or drag.",
        rows=[
            ("Bullish", str(sentiment.get("bullish", 0))),
            ("Neutral", str(sentiment.get("neutral", 0))),
            ("Bearish", str(sentiment.get("bearish", 0))),
        ]
        if sentiment
        else [("Status", "Waiting on sentiment data")],
    )
    st.markdown("")
    if alerts:
        render_note_card(
            "Alert stack",
            "Unread items stay visible without flooding the page, giving the dashboard a clear secondary rhythm.",
            rows=[(alert["title"], "Unread" if not alert["is_read"] else "Read") for alert in alerts[:4]],
        )
    else:
        render_note_card(
            "Alert stack",
            "No fresh alerts right now. When rebalancing drift or signal changes occur, they will surface here.",
        )
    st.markdown("")
    render_note_card(
        "Why this layout feels different",
        "The main lane handles action, while the right rail carries atmosphere and context. That keeps the dashboard from turning into a flat wall of widgets.",
        rows=[
            ("Poster moment", "Hero frames the page"),
            ("Data rhythm", "Primary lane then side rail"),
            ("Framework fit", "Pure Streamlit + CSS"),
        ],
    )
