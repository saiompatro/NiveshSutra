"""Stock detail page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import plotly.graph_objects as go
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
    style_plotly_figure,
)
from supabase_client import get_anon_client, get_authed_client
from utils import signal_badge_html

st.set_page_config(page_title="Stock Detail | NiveshSutra", layout="wide")
apply_theme()
require_auth()


def _render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page="Stocks",
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
        headline="Move from the catalog to a single-name story: price action, technicals, and sentiment in one frame.",
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.switch_page("app.py")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_stock_info(symbol: str) -> dict:
    try:
        return (
            get_anon_client().table("stocks").select("*").eq("symbol", symbol).single().execute().data
            or {}
        )
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlcv(symbol: str, days: int = 365) -> list[dict]:
    try:
        rows = (
            get_anon_client()
            .table("ohlcv")
            .select("date, open, high, low, close, volume")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(days)
            .execute()
            .data
            or []
        )
        return sorted(rows, key=lambda row: row["date"])
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def fetch_indicators(symbol: str, days: int = 120) -> list[dict]:
    try:
        rows = (
            get_anon_client()
            .table("technical_indicators")
            .select("*")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(days)
            .execute()
            .data
            or []
        )
        return sorted(rows, key=lambda row: row["date"])
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def fetch_sentiment(symbol: str, days: int = 60) -> list[dict]:
    try:
        rows = (
            get_anon_client()
            .table("sentiment_daily")
            .select("date, avg_sentiment, article_count")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(days)
            .execute()
            .data
            or []
        )
        return sorted(rows, key=lambda row: row["date"])
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def fetch_latest_signal(symbol: str) -> dict | None:
    try:
        rows = (
            get_anon_client()
            .table("signals")
            .select("*")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def is_in_watchlist(symbol: str, user_id: str, access_token: str) -> bool:
    try:
        rows = (
            get_authed_client(access_token)
            .table("watchlist")
            .select("symbol")
            .eq("user_id", user_id)
            .eq("symbol", symbol)
            .execute()
            .data
            or []
        )
        return len(rows) > 0
    except Exception:
        return False


def toggle_watchlist(symbol: str, user_id: str, access_token: str, add: bool) -> None:
    client = get_authed_client(access_token)
    if add:
        client.table("watchlist").upsert(
            {"user_id": user_id, "symbol": symbol},
            on_conflict="user_id,symbol",
        ).execute()
    else:
        client.table("watchlist").delete().eq("user_id", user_id).eq("symbol", symbol).execute()


_render_sidebar()
symbol = st.session_state.get("selected_stock")

if not symbol:
    render_empty_state("No stock selected", "Return to the Stocks page and open a symbol to continue.")
    if st.button("Back to Stocks", use_container_width=True):
        st.switch_page("pages/2_Stocks.py")
    st.stop()

token = get_access_token()
user_id = get_user_id()

with st.spinner("Loading stock detail..."):
    info = fetch_stock_info(symbol)
    ohlcv = fetch_ohlcv(symbol)
    indicators = fetch_indicators(symbol)
    sentiment_data = fetch_sentiment(symbol)
    latest_signal = fetch_latest_signal(symbol)
    in_watchlist = is_in_watchlist(symbol, user_id, token)

company = info.get("company_name", symbol)
sector = info.get("sector", "Sector pending")
latest = ohlcv[-1] if ohlcv else {}
previous = ohlcv[-2] if len(ohlcv) > 1 else latest
price = float(latest.get("close", 0) or 0)
previous_close = float(previous.get("close", price) or price)
price_change = price - previous_close
price_change_pct = (price_change / previous_close * 100) if previous_close else 0.0

render_page_hero(
    kicker="Single-name story",
    title=f"{symbol} | {company}",
    body=(
        "A full-screen reading of price structure, technical tone, and sentiment drift. This view is built to feel like an analyst tear sheet rather than a generic ticker page."
    ),
    pills=[
        sector,
        "In watchlist" if in_watchlist else "Not in watchlist",
        f"Move {price_change_pct:+.2f}%",
    ],
    aside_title="Current read",
    aside_rows=[
        ("Last price", f"{price:,.2f}"),
        ("Daily move", f"{price_change:+.2f}"),
        ("Latest signal", latest_signal.get("signal", "Waiting") if latest_signal else "Waiting"),
    ],
)

action_left, action_right = st.columns([1, 1.2], gap="medium")
with action_left:
    if st.button("Back to Stocks", use_container_width=True):
        st.switch_page("pages/2_Stocks.py")
with action_right:
    watch_label = "Remove from watchlist" if in_watchlist else "Add to watchlist"
    if st.button(watch_label, use_container_width=True):
        toggle_watchlist(symbol, user_id, token, add=not in_watchlist)
        st.rerun()

render_metric_grid(
    [
        {
            "label": "Last price",
            "value": f"{price:,.2f}",
            "detail": f"Daily move {price_change:+.2f} | {price_change_pct:+.2f}%",
            "tone": "emerald" if price_change >= 0 else "rose",
        },
        {
            "label": "Session range",
            "value": f"{float(latest.get('low', 0) or 0):,.2f} - {float(latest.get('high', 0) or 0):,.2f}",
            "detail": f"Open {float(latest.get('open', 0) or 0):,.2f}",
            "tone": "amber",
        },
        {
            "label": "Volume",
            "value": f"{int(latest.get('volume', 0) or 0):,}",
            "detail": "Latest recorded turnover in the local OHLCV store.",
            "tone": "amber",
        },
        {
            "label": "Signal",
            "value": latest_signal.get("signal", "Waiting").replace("_", " ").title() if latest_signal else "Waiting",
            "detail": f"Confidence {(latest_signal.get('confidence', 0) or 0) * 100:.0f}%"
            if latest_signal
            else "Signal generation has not landed for this name yet.",
            "tone": "emerald" if latest_signal and latest_signal.get("signal") in {"buy", "strong_buy"} else "rose" if latest_signal and latest_signal.get("signal") in {"sell", "strong_sell"} else "amber",
        },
    ],
    columns=4,
)

if latest_signal:
    render_info_band(
        "Signal context",
        f"{symbol} currently carries {latest_signal['signal'].replace('_', ' ').title()} status. "
        f"Use the chart, indicator, and sentiment tabs below to sanity-check whether the signal fits your own read.",
    )

tab_chart, tab_indicators, tab_sentiment = st.tabs(["Chart", "Indicators", "Sentiment"])

with tab_chart:
    render_section_heading(
        "Price structure",
        "Candles, moving averages, and zoom controls framed as the lead analytical surface.",
        kicker="Primary read",
    )
    range_choice = st.radio("Range", ["30d", "90d", "180d", "1Y"], horizontal=True, index=1)
    day_map = {"30d": 30, "90d": 90, "180d": 180, "1Y": 365}
    subset = ohlcv[-day_map[range_choice] :] if ohlcv else []

    if subset:
        dates = [row["date"] for row in subset]
        opens = [float(row["open"]) for row in subset]
        highs = [float(row["high"]) for row in subset]
        lows = [float(row["low"]) for row in subset]
        closes = [float(row["close"]) for row in subset]
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name=symbol,
                increasing_line_color="#5de4c7",
                decreasing_line_color="#ff7f90",
            )
        )
        if indicators:
            sma20_rows = [(row["date"], row["sma_20"]) for row in indicators if row.get("sma_20")]
            sma50_rows = [(row["date"], row["sma_50"]) for row in indicators if row.get("sma_50")]
            if sma20_rows:
                fig.add_trace(
                    go.Scatter(
                        x=[row[0] for row in sma20_rows],
                        y=[row[1] for row in sma20_rows],
                        name="SMA 20",
                        line=dict(color="#7bc8ff", width=1.6),
                    )
                )
            if sma50_rows:
                fig.add_trace(
                    go.Scatter(
                        x=[row[0] for row in sma50_rows],
                        y=[row[1] for row in sma50_rows],
                        name="SMA 50",
                        line=dict(color="#f3a45c", width=1.6, dash="dot"),
                    )
                )
        fig.update_layout(xaxis=dict(rangeslider=dict(visible=False)))
        st.plotly_chart(style_plotly_figure(fig, height=460), use_container_width=True)
    else:
        render_empty_state("No OHLCV data available", "Price history has not been populated for this stock yet.")

with tab_indicators:
    render_section_heading(
        "Technical stack",
        "Momentum, volatility, and structure framed for a quick read before acting on a signal.",
        kicker="Indicator lane",
    )
    if indicators:
        latest_indicators = indicators[-1]
        render_metric_grid(
            [
                {
                    "label": "RSI 14",
                    "value": f"{latest_indicators.get('rsi_14', 0):.1f}" if latest_indicators.get("rsi_14") is not None else "n/a",
                    "detail": "Below 30 is oversold | above 70 is overbought.",
                    "tone": "amber",
                },
                {
                    "label": "MACD",
                    "value": f"{latest_indicators.get('macd', 0):.3f}" if latest_indicators.get("macd") is not None else "n/a",
                    "detail": f"Signal {latest_indicators.get('macd_signal', 0):.3f}" if latest_indicators.get("macd_signal") is not None else "Signal line unavailable.",
                    "tone": "emerald",
                },
                {
                    "label": "ATR 14",
                    "value": f"{latest_indicators.get('atr_14', 0):.2f}" if latest_indicators.get("atr_14") is not None else "n/a",
                    "detail": "Average true range as a volatility proxy.",
                    "tone": "rose",
                },
                {
                    "label": "Trend anchor",
                    "value": f"{latest_indicators.get('sma_20', 0):.2f}" if latest_indicators.get("sma_20") is not None else "n/a",
                    "detail": f"SMA 50 {latest_indicators.get('sma_50', 0):.2f}" if latest_indicators.get("sma_50") is not None else "Longer moving average unavailable.",
                    "tone": "amber",
                },
            ],
            columns=4,
        )
        rsi_rows = [(row["date"], row["rsi_14"]) for row in indicators if row.get("rsi_14") is not None]
        if rsi_rows:
            fig_rsi = go.Figure()
            fig_rsi.add_trace(
                go.Scatter(
                    x=[row[0] for row in rsi_rows],
                    y=[row[1] for row in rsi_rows],
                    name="RSI 14",
                    line=dict(color="#7bc8ff", width=2),
                )
            )
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ff7f90")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#5de4c7")
            fig_rsi.update_layout(yaxis=dict(range=[0, 100]))
            st.plotly_chart(style_plotly_figure(fig_rsi, height=280), use_container_width=True)
    else:
        render_empty_state("Indicator pipeline has not landed", "Run the technical indicator pipeline to populate this tab.")

with tab_sentiment:
    render_section_heading(
        "Headline drift",
        "FinBERT sentiment translated into a readable emotional contour for the stock.",
        kicker="Narrative layer",
    )
    if sentiment_data:
        dates = [row["date"] for row in sentiment_data]
        scores = [float(row["avg_sentiment"]) for row in sentiment_data]
        counts = [int(row.get("article_count", 0)) for row in sentiment_data]
        fig_sentiment = go.Figure()
        fig_sentiment.add_trace(
            go.Scatter(
                x=dates,
                y=scores,
                name="Average sentiment",
                fill="tozeroy",
                line=dict(color="#5de4c7", width=2.2),
            )
        )
        fig_sentiment.add_hline(y=0, line_color="rgba(164,185,213,0.25)")
        fig_sentiment.update_layout(yaxis=dict(range=[-1, 1]))
        st.plotly_chart(style_plotly_figure(fig_sentiment, height=320), use_container_width=True)

        latest_score = scores[-1] if scores else 0.0
        sentiment_label = "Bullish" if latest_score > 0.1 else "Bearish" if latest_score < -0.1 else "Neutral"
        rail_left, rail_right = st.columns(2, gap="large")
        with rail_left:
            render_note_card(
                "Current read",
                "Use the latest FinBERT output as a narrative check against the technical picture above.",
                rows=[
                    ("Mood", sentiment_label),
                    ("Latest score", f"{latest_score:.3f}"),
                    ("Articles", str(counts[-1] if counts else 0)),
                ],
            )
        with rail_right:
            render_note_card(
                "Why the page works",
                "The detail view makes one stock feel significant. Instead of a generic ticker sheet, the layout gives each analytical layer a distinct role.",
                rows=[
                    ("Lead surface", "Chart first"),
                    ("Support lane", "Indicators"),
                    ("Narrative lane", "Sentiment"),
                ],
            )
    else:
        render_empty_state("No sentiment history available", "Run the sentiment pipeline to unlock this narrative layer.")
