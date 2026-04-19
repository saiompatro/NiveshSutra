"""Stock Detail — candlestick chart, technical indicators, sentiment, news."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
from auth import require_auth, get_access_token, get_user_id
from supabase_client import get_anon_client, get_authed_client
from utils import signal_badge_html, format_signal

st.set_page_config(page_title="Stock Detail — NiveshSutra", page_icon="📉", layout="wide")
require_auth()


# ---------------------------------------------------------------------------
# Resolve symbol
# ---------------------------------------------------------------------------

symbol = st.session_state.get("selected_stock")
if not symbol:
    st.warning("No stock selected. Please go back to Stocks.")
    if st.button("← Back to Stocks"):
        st.switch_page("pages/2_Stocks.py")
    st.stop()


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_stock_info(symbol: str) -> dict:
    try:
        return (
            get_anon_client()
            .table("stocks")
            .select("*")
            .eq("symbol", symbol)
            .single()
            .execute()
            .data or {}
        )
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlcv(symbol: str, days: int = 180) -> list:
    try:
        rows = (
            get_anon_client()
            .table("ohlcv")
            .select("date, open, high, low, close, volume")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(days)
            .execute()
            .data or []
        )
        return sorted(rows, key=lambda r: r["date"])
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def fetch_indicators(symbol: str, days: int = 60) -> list:
    try:
        rows = (
            get_anon_client()
            .table("technical_indicators")
            .select("*")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(days)
            .execute()
            .data or []
        )
        return sorted(rows, key=lambda r: r["date"])
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def fetch_sentiment(symbol: str, days: int = 30) -> list:
    try:
        rows = (
            get_anon_client()
            .table("sentiment_daily")
            .select("date, avg_sentiment, article_count")
            .eq("symbol", symbol)
            .order("date", desc=True)
            .limit(days)
            .execute()
            .data or []
        )
        return sorted(rows, key=lambda r: r["date"])
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
            .data or []
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
            .data or []
        )
        return len(rows) > 0
    except Exception:
        return False


def toggle_watchlist(symbol: str, user_id: str, access_token: str, add: bool):
    client = get_authed_client(access_token)
    if add:
        client.table("watchlist").upsert(
            {"user_id": user_id, "symbol": symbol}, on_conflict="user_id,symbol"
        ).execute()
    else:
        client.table("watchlist").delete().eq("user_id", user_id).eq("symbol", symbol).execute()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

token = get_access_token()
uid = get_user_id()

c_back, c_title, c_watchbtn = st.columns([1, 6, 2])
with c_back:
    if st.button("← Stocks"):
        st.switch_page("pages/2_Stocks.py")

with st.spinner("Loading stock data…"):
    info = fetch_stock_info(symbol)
    ohlcv = fetch_ohlcv(symbol)
    indicators = fetch_indicators(symbol)
    sentiment_data = fetch_sentiment(symbol)
    latest_signal = fetch_latest_signal(symbol)
    in_watchlist = is_in_watchlist(symbol, uid, token)

with c_title:
    company = info.get("company_name", symbol)
    sector = info.get("sector", "")
    st.markdown(f"## {symbol} — {company}")
    if sector:
        st.caption(f"Sector: {sector}")

with c_watchbtn:
    label = "★ Remove from Watchlist" if in_watchlist else "☆ Add to Watchlist"
    if st.button(label, use_container_width=True):
        toggle_watchlist(symbol, uid, token, add=not in_watchlist)
        st.rerun()

# Current price from latest ohlcv
if ohlcv:
    latest = ohlcv[-1]
    prev = ohlcv[-2] if len(ohlcv) > 1 else latest
    price = float(latest["close"])
    prev_close = float(prev["close"])
    chg = price - prev_close
    chg_pct = (chg / prev_close * 100) if prev_close else 0.0
    chg_color = "#22c55e" if chg >= 0 else "#ef4444"

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Price (₹)", f"{price:,.2f}", f"{chg:+.2f} ({chg_pct:+.2f}%)")
    m2.metric("Open", f"{float(latest.get('open', 0)):,.2f}")
    m3.metric("High", f"{float(latest.get('high', 0)):,.2f}")
    m4.metric("Low", f"{float(latest.get('low', 0)):,.2f}")
    m5.metric("Volume", f"{int(latest.get('volume', 0)):,}")

# Signal badge
if latest_signal:
    col_sig, _ = st.columns([2, 8])
    with col_sig:
        sig = latest_signal.get("signal", "")
        conf = latest_signal.get("confidence", 0) or 0
        st.markdown(
            f"{signal_badge_html(sig)} "
            f"<span style='font-size:0.8rem;color:#94a3b8'>confidence: {conf * 100:.0f}%</span>",
            unsafe_allow_html=True,
        )

st.divider()

# ---------------------------------------------------------------------------
# Tabs: Chart | Indicators | Sentiment
# ---------------------------------------------------------------------------

tab_chart, tab_ind, tab_sent = st.tabs(["📊 Chart", "📐 Indicators", "🗞️ Sentiment"])

with tab_chart:
    days_choice = st.radio("Range", ["30d", "90d", "180d", "1Y"], horizontal=True, index=1)
    day_map = {"30d": 30, "90d": 90, "180d": 180, "1Y": 365}
    n = day_map[days_choice]
    subset = ohlcv[-n:] if len(ohlcv) > n else ohlcv

    if subset:
        dates = [r["date"] for r in subset]
        opens = [float(r["open"]) for r in subset]
        highs = [float(r["high"]) for r in subset]
        lows = [float(r["low"]) for r in subset]
        closes = [float(r["close"]) for r in subset]
        volumes = [int(r.get("volume", 0)) for r in subset]

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=dates, open=opens, high=highs, low=lows, close=closes,
            name=symbol,
            increasing_line_color="#22c55e", decreasing_line_color="#ef4444",
        ))

        # Overlay SMA20/SMA50 from indicators if available
        if indicators:
            ind_dates = [r["date"] for r in indicators if r.get("sma_20")]
            sma20 = [r.get("sma_20") for r in indicators if r.get("sma_20")]
            sma50 = [r.get("sma_50") for r in indicators if r.get("sma_50")]
            ind50_dates = [r["date"] for r in indicators if r.get("sma_50")]
            if sma20:
                fig.add_trace(go.Scatter(
                    x=ind_dates, y=sma20, name="SMA 20",
                    line=dict(color="#3b82f6", width=1, dash="dot"),
                ))
            if sma50:
                fig.add_trace(go.Scatter(
                    x=ind50_dates, y=sma50, name="SMA 50",
                    line=dict(color="#f59e0b", width=1, dash="dot"),
                ))

        fig.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#f1f5f9"),
            xaxis=dict(gridcolor="#1e293b", rangeslider=dict(visible=False)),
            yaxis=dict(gridcolor="#1e293b"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=0, r=0, t=10, b=0),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No OHLCV data available for this stock.")

with tab_ind:
    if indicators:
        latest_ind = indicators[-1]
        st.markdown("**Latest Technical Indicators**")
        i1, i2, i3, i4 = st.columns(4)
        rsi = latest_ind.get("rsi_14")
        i1.metric("RSI (14)", f"{rsi:.1f}" if rsi else "—",
                  help="< 30 oversold | > 70 overbought")
        macd = latest_ind.get("macd")
        macd_sig = latest_ind.get("macd_signal")
        i2.metric("MACD", f"{macd:.3f}" if macd else "—")
        i3.metric("MACD Signal", f"{macd_sig:.3f}" if macd_sig else "—")
        atr = latest_ind.get("atr_14")
        i4.metric("ATR (14)", f"{atr:.2f}" if atr else "—", help="Average True Range (volatility)")

        i5, i6, i7, i8 = st.columns(4)
        bb_u = latest_ind.get("bb_upper")
        bb_l = latest_ind.get("bb_lower")
        sma20 = latest_ind.get("sma_20")
        sma50 = latest_ind.get("sma_50")
        i5.metric("BB Upper", f"{bb_u:.2f}" if bb_u else "—")
        i6.metric("BB Lower", f"{bb_l:.2f}" if bb_l else "—")
        i7.metric("SMA 20", f"{sma20:.2f}" if sma20 else "—")
        i8.metric("SMA 50", f"{sma50:.2f}" if sma50 else "—")

        st.divider()

        # RSI line chart
        rsi_vals = [(r["date"], r["rsi_14"]) for r in indicators if r.get("rsi_14")]
        if rsi_vals:
            dates_r, rsi_v = zip(*rsi_vals)
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=list(dates_r), y=list(rsi_v), name="RSI 14",
                                         line=dict(color="#3b82f6", width=2)))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef4444", annotation_text="Overbought 70")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#22c55e", annotation_text="Oversold 30")
            fig_rsi.update_layout(
                paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                font=dict(color="#f1f5f9"),
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b", range=[0, 100]),
                height=220, margin=dict(l=0, r=0, t=20, b=0),
                title="RSI (14)",
            )
            st.plotly_chart(fig_rsi, use_container_width=True)
    else:
        st.info("No indicator data available. Run the ML ingest pipeline first.")

with tab_sent:
    if sentiment_data:
        dates_s = [r["date"] for r in sentiment_data]
        scores = [float(r["avg_sentiment"]) for r in sentiment_data]
        counts = [int(r.get("article_count", 0)) for r in sentiment_data]

        fig_sent = go.Figure()
        fig_sent.add_trace(go.Scatter(
            x=dates_s, y=scores, name="Avg Sentiment",
            fill="tozeroy",
            line=dict(color="#3b82f6", width=2),
        ))
        fig_sent.add_hline(y=0, line_color="#475569")
        fig_sent.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#f1f5f9"),
            xaxis=dict(gridcolor="#1e293b"),
            yaxis=dict(gridcolor="#1e293b", range=[-1, 1]),
            height=280, margin=dict(l=0, r=0, t=20, b=0),
            title="Daily Sentiment Score (FinBERT)",
        )
        st.plotly_chart(fig_sent, use_container_width=True)

        avg_now = scores[-1] if scores else 0.0
        label = "Bullish" if avg_now > 0.1 else ("Bearish" if avg_now < -0.1 else "Neutral")
        c_label, c_count = st.columns(2)
        c_label.metric("Current Sentiment", label, f"{avg_now:.3f}")
        c_count.metric("Articles (latest)", counts[-1] if counts else 0)
    else:
        st.info("No sentiment data available. Run the sentiment pipeline first.")
