"""Stocks page: browse/filter stocks and add symbols through the FastAPI service."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from api_client import request_json
from auth import get_access_token, require_auth
from supabase_client import get_anon_client
from utils import signal_badge_html

st.set_page_config(page_title="Stocks - NiveshSutra", page_icon="📋", layout="wide")
require_auth()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_stocks(nifty50_only: bool = False) -> list[dict]:
    """Fetch stocks with latest close price and signal."""
    client = get_anon_client()
    query = client.table("stocks").select("symbol, company_name, sector, is_nifty50, yf_ticker").eq("active", True)
    if nifty50_only:
        query = query.eq("is_nifty50", True)
    stocks = query.order("symbol").execute().data or []

    sig_rows = (
        client.table("signals")
        .select("symbol, signal, date")
        .order("date", desc=True)
        .limit(max(50, len(stocks) * 2))
        .execute()
        .data
        or []
    )
    signal_map: dict[str, str] = {}
    for row in sig_rows:
        signal_map.setdefault(row["symbol"], row["signal"])

    symbols = [stock["symbol"] for stock in stocks]
    price_map: dict[str, dict] = {}
    if symbols:
        ohlcv = (
            client.table("ohlcv")
            .select("symbol, close, date")
            .in_("symbol", symbols)
            .order("date", desc=True)
            .limit(len(symbols) * 2)
            .execute()
            .data
            or []
        )
        grouped: dict[str, list] = {}
        for row in ohlcv:
            grouped.setdefault(row["symbol"], [])
            if len(grouped[row["symbol"]]) < 2:
                grouped[row["symbol"]].append(row)
        for symbol, rows in grouped.items():
            latest = float(rows[0]["close"]) if rows else 0.0
            previous = float(rows[1]["close"]) if len(rows) > 1 else latest
            change_pct = ((latest - previous) / previous * 100) if previous else 0.0
            price_map[symbol] = {"price": latest, "change_pct": change_pct}

    enriched = []
    for stock in stocks:
        price_data = price_map.get(stock["symbol"], {"price": 0.0, "change_pct": 0.0})
        enriched.append(
            {
                "symbol": stock["symbol"],
                "company_name": stock.get("company_name") or "",
                "sector": stock.get("sector") or "",
                "is_nifty50": stock.get("is_nifty50", False),
                "price": price_data["price"],
                "change_pct": price_data["change_pct"],
                "signal": signal_map.get(stock["symbol"], ""),
            }
        )
    return enriched


def add_stock(symbol: str, access_token: str) -> tuple[bool, str]:
    """Validate and add a symbol through the FastAPI backend."""
    try:
        payload = request_json(
            "GET",
            "/api/v1/stocks/search",
            access_token=access_token,
            params={"q": symbol.upper()},
        )
        stock = payload.get("stock") or {}
        added_symbol = stock.get("symbol") or symbol.upper()
        source = payload.get("source")
        suffix = f" via {source}" if source else ""
        return True, f"{added_symbol} added successfully{suffix}"
    except Exception as exc:
        return False, str(exc)


st.title("Stocks")
st.caption("Indian equity stocks with AI-powered signals")

ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 1, 1])
with ctrl1:
    search = st.text_input("Search symbol or company", placeholder="e.g. RELIANCE, Infosys")
with ctrl2:
    stocks_raw = fetch_stocks()
    sectors = sorted({stock["sector"] for stock in stocks_raw if stock["sector"]})
    sector_filter = st.selectbox("Sector", ["All Sectors"] + sectors)
with ctrl3:
    universe = st.radio("Universe", ["All", "Nifty 50"], horizontal=True)
with ctrl4:
    add_clicked = st.button("Add Stock", use_container_width=True)

if add_clicked:
    st.session_state["show_add_form"] = True

if st.session_state.get("show_add_form"):
    with st.form("add_stock_form"):
        st.markdown("**Add a stock by NSE symbol**")
        new_symbol = st.text_input("NSE Symbol (e.g. IRCTC)", key="add_sym")
        c1, c2 = st.columns(2)
        submit = c1.form_submit_button("Add", use_container_width=True)
        cancel = c2.form_submit_button("Cancel", use_container_width=True)
    if cancel:
        st.session_state["show_add_form"] = False
        st.rerun()
    if submit and new_symbol.strip():
        with st.spinner(f"Looking up {new_symbol.upper()}..."):
            ok, message = add_stock(new_symbol.strip().upper(), get_access_token())
        if ok:
            st.success(message)
            fetch_stocks.clear()
            st.session_state["show_add_form"] = False
            st.rerun()
        else:
            st.error(f"Failed: {message}")

nifty_only = universe == "Nifty 50"
stocks = fetch_stocks(nifty_only)

if search:
    query = search.lower()
    stocks = [stock for stock in stocks if query in stock["symbol"].lower() or query in stock["company_name"].lower()]
if sector_filter != "All Sectors":
    stocks = [stock for stock in stocks if stock["sector"] == sector_filter]

st.caption(f"Showing {len(stocks)} stocks")

header = st.columns([2, 4, 3, 2, 2, 2])
header[0].markdown("**Symbol**")
header[1].markdown("**Company**")
header[2].markdown("**Sector**")
header[3].markdown("**Price (INR)**")
header[4].markdown("**Change %**")
header[5].markdown("**Signal**")
st.markdown("<hr style='margin:4px 0 8px'>", unsafe_allow_html=True)

for stock in stocks:
    row = st.columns([2, 4, 3, 2, 2, 2])
    change_pct = stock["change_pct"]
    change_color = "#22c55e" if change_pct >= 0 else "#ef4444"

    row[0].markdown(f"**{stock['symbol']}**")
    row[1].markdown(stock["company_name"])
    row[2].markdown(f"<span style='color:#94a3b8'>{stock['sector']}</span>", unsafe_allow_html=True)
    row[3].markdown(f"{stock['price']:,.2f}")
    row[4].markdown(
        f"<span style='color:{change_color}'>{'+' if change_pct >= 0 else ''}{change_pct:.2f}%</span>",
        unsafe_allow_html=True,
    )
    if stock["signal"]:
        row[5].markdown(signal_badge_html(stock["signal"]), unsafe_allow_html=True)
    else:
        row[5].markdown("<span style='color:#475569'>-</span>", unsafe_allow_html=True)

    with row[0]:
        if st.button("->", key=f"goto_{stock['symbol']}", help=f"View {stock['symbol']}"):
            st.session_state["selected_stock"] = stock["symbol"]
            st.switch_page("pages/3_Stock_Detail.py")

    st.markdown("<hr style='margin:2px 0;border-color:#1e293b'>", unsafe_allow_html=True)
