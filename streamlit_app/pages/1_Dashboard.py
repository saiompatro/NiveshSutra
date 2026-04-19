"""Dashboard — portfolio overview, Nifty 50, sentiment, signals, watchlist, alerts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from auth import require_auth, get_access_token, get_user_id, get_profile
from supabase_client import get_anon_client, get_authed_client
from utils import format_currency, format_pct, signal_badge_html, signal_color, format_signal

st.set_page_config(page_title="Dashboard — NiveshSutra", page_icon="📊", layout="wide")
require_auth()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _supabase():
    return get_authed_client(get_access_token())


@st.cache_data(ttl=60, show_spinner=False)
def fetch_portfolio_performance(user_id: str, access_token: str) -> dict:
    try:
        client = get_authed_client(access_token)
        holdings = (
            client.table("holdings")
            .select("symbol, quantity, avg_buy_price")
            .eq("user_id", user_id)
            .execute()
            .data or []
        )
        if not holdings:
            return {}
        total_invested = 0.0
        current_value = 0.0
        for h in holdings:
            ohlcv = (
                get_anon_client()
                .table("ohlcv")
                .select("close")
                .eq("symbol", h["symbol"])
                .order("date", desc=True)
                .limit(1)
                .execute()
                .data
            )
            price = float(ohlcv[0]["close"]) if ohlcv else float(h["avg_buy_price"])
            invested = float(h["quantity"]) * float(h["avg_buy_price"])
            value = float(h["quantity"]) * price
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


@st.cache_data(ttl=60, show_spinner=False)
def fetch_nifty50() -> dict:
    try:
        data = (
            get_anon_client()
            .table("ohlcv")
            .select("close, date")
            .eq("symbol", "^NSEI")
            .order("date", desc=True)
            .limit(2)
            .execute()
            .data or []
        )
        if not data:
            return {}
        latest = float(data[0]["close"])
        prev = float(data[1]["close"]) if len(data) > 1 else latest
        change = latest - prev
        change_pct = (change / prev * 100) if prev else 0.0
        return {"value": latest, "change": change, "change_pct": change_pct}
    except Exception:
        return {}


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
            .data or []
        )
        if not result:
            return {}
        latest_date = result[0]["date"]
        today = [r for r in result if r["date"] == latest_date]
        scores = [float(r["avg_sentiment"]) for r in today]
        avg = sum(scores) / len(scores) if scores else 0.0
        bullish = sum(1 for s in scores if s > 0.1)
        bearish = sum(1 for s in scores if s < -0.1)
        neutral = len(scores) - bullish - bearish
        label = "Bullish" if avg > 0.1 else ("Bearish" if avg < -0.1 else "Neutral")
        return {
            "overall": label,
            "score": avg,
            "bullish": bullish,
            "neutral": neutral,
            "bearish": bearish,
            "total": len(scores),
        }
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_latest_signals(limit: int = 5) -> list:
    try:
        rows = (
            get_anon_client()
            .table("signals")
            .select("symbol, signal, confidence, created_at")
            .order("created_at", desc=True)
            .limit(limit * 2)
            .execute()
            .data or []
        )
        seen, latest = set(), []
        for r in rows:
            if r["symbol"] not in seen:
                seen.add(r["symbol"])
                latest.append(r)
            if len(latest) >= limit:
                break
        return latest
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_watchlist_live(user_id: str, access_token: str) -> list:
    try:
        client = get_authed_client(access_token)
        rows = (
            client.table("watchlist")
            .select("symbol, stocks(company_name)")
            .eq("user_id", user_id)
            .order("added_at", desc=True)
            .limit(8)
            .execute()
            .data or []
        )
        enriched = []
        for r in rows:
            stock_info = r.get("stocks") or {}
            ohlcv = (
                get_anon_client()
                .table("ohlcv")
                .select("close, date")
                .eq("symbol", r["symbol"])
                .order("date", desc=True)
                .limit(2)
                .execute()
                .data or []
            )
            price = float(ohlcv[0]["close"]) if ohlcv else 0.0
            prev = float(ohlcv[1]["close"]) if len(ohlcv) > 1 else price
            change_pct = ((price - prev) / prev * 100) if prev else 0.0
            enriched.append({
                "symbol": r["symbol"],
                "company_name": stock_info.get("company_name", ""),
                "price": price,
                "change_pct": change_pct,
            })
        return enriched
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def fetch_alerts(user_id: str, access_token: str, limit: int = 5) -> list:
    try:
        client = get_authed_client(access_token)
        return (
            client.table("alerts")
            .select("id, title, message, is_read, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data or []
        )
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

st.title("Dashboard")
st.caption("Your portfolio overview and market insights")

token = get_access_token()
uid = get_user_id()

with st.spinner("Loading dashboard…"):
    portfolio = fetch_portfolio_performance(uid, token)
    nifty = fetch_nifty50()
    sentiment = fetch_market_sentiment()
    signals = fetch_latest_signals()
    watchlist = fetch_watchlist_live(uid, token)
    alerts = fetch_alerts(uid, token)

# -- Top row: 3 metric cards --
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("💼 Portfolio Value")
    if portfolio:
        st.metric(
            label="Current Value",
            value=format_currency(portfolio["total_value"]),
            delta=f"{format_pct(portfolio['total_pnl_pct'])} ({format_currency(portfolio['total_pnl'])})",
            delta_color="normal",
        )
        st.caption(f"Invested: {format_currency(portfolio['total_invested'])}")
    else:
        st.info("No holdings yet. Go to Portfolio to add your first stock.")

with col2:
    st.subheader("📈 Nifty 50")
    if nifty:
        st.metric(
            label="Index Value",
            value=f"{nifty['value']:,.2f}",
            delta=f"{format_pct(nifty['change_pct'])} ({nifty['change']:+.2f})",
            delta_color="normal",
        )
    else:
        st.info("Market data unavailable")

with col3:
    st.subheader("🧠 Market Sentiment")
    if sentiment:
        color = {"Bullish": "green", "Bearish": "red", "Neutral": "orange"}.get(
            sentiment["overall"], "gray"
        )
        st.markdown(
            f"<h2 style='color:{color};margin:0'>{sentiment['overall']}</h2>"
            f"<p style='margin:0;color:#94a3b8;font-size:0.85rem'>"
            f"Score: {sentiment['score']:.3f}</p>",
            unsafe_allow_html=True,
        )
        total = sentiment["total"] or 1
        st.markdown(
            f"<div style='display:flex;gap:16px;margin-top:8px;font-size:0.8rem'>"
            f"<span style='color:#22c55e'>▲ Bullish: {sentiment['bullish']}</span>"
            f"<span style='color:#eab308'>◆ Neutral: {sentiment['neutral']}</span>"
            f"<span style='color:#ef4444'>▼ Bearish: {sentiment['bearish']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        # Stacked progress bar via columns
        if total > 0:
            b_pct = sentiment["bullish"] / total
            n_pct = sentiment["neutral"] / total
            cols = st.columns([max(b_pct, 0.01), max(n_pct, 0.01), max(1 - b_pct - n_pct, 0.01)])
            cols[0].markdown(
                "<div style='background:#22c55e;height:6px;border-radius:3px'></div>",
                unsafe_allow_html=True,
            )
            cols[1].markdown(
                "<div style='background:#eab308;height:6px;border-radius:3px'></div>",
                unsafe_allow_html=True,
            )
            cols[2].markdown(
                "<div style='background:#ef4444;height:6px;border-radius:3px'></div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Sentiment data unavailable")

st.divider()

# -- Bottom row: Signals | Watchlist | Alerts --
col_sig, col_watch, col_alerts = st.columns(3)

with col_sig:
    st.subheader("⚡ Latest Signals")
    if signals:
        for s in signals:
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(
                    f"**[{s['symbol']}](/stocks/{s['symbol']})**  \n"
                    f"<span style='font-size:0.75rem;color:#94a3b8'>"
                    f"Confidence: {s.get('confidence', 0) * 100:.0f}%</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(signal_badge_html(s["signal"]), unsafe_allow_html=True)
        if st.button("View all signals →", key="dash_sig"):
            st.switch_page("pages/4_Signals.py")
    else:
        st.info("No signals available yet.")

with col_watch:
    st.subheader("👁️ Watchlist")
    if watchlist:
        for item in watchlist:
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(
                    f"**{item['symbol']}**  \n"
                    f"<span style='font-size:0.75rem;color:#94a3b8'>{item['company_name'][:22]}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                chg = item["change_pct"]
                color = "#22c55e" if chg >= 0 else "#ef4444"
                st.markdown(
                    f"<div style='text-align:right'>"
                    f"<span style='font-weight:600'>{item['price']:,.2f}</span><br>"
                    f"<span style='color:{color};font-size:0.78rem'>{format_pct(chg)}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("Watchlist empty. Browse Stocks to add.")
        if st.button("Browse Stocks →", key="dash_stocks"):
            st.switch_page("pages/2_Stocks.py")

with col_alerts:
    st.subheader("🔔 Alerts")
    if alerts:
        for a in alerts:
            border = "#3b82f6" if not a["is_read"] else "#334155"
            bg = "#1e3a5f" if not a["is_read"] else "transparent"
            st.markdown(
                f"<div style='border:1px solid {border};background:{bg};"
                f"border-radius:6px;padding:8px 12px;margin-bottom:6px'>"
                f"<strong style='font-size:0.85rem'>{a['title']}</strong><br>"
                f"<span style='font-size:0.75rem;color:#94a3b8'>{a['message']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No alerts.")
