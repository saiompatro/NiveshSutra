"""Stocks — browse/filter Nifty 50 + all stocks, add custom stocks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from auth import require_auth, get_access_token
from supabase_client import get_anon_client, get_authed_client
from utils import signal_badge_html, format_signal, signal_color

st.set_page_config(page_title="Stocks — NiveshSutra", page_icon="📋", layout="wide")
require_auth()


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def fetch_stocks(nifty50_only: bool = False) -> list:
    """Fetch stocks with latest close price and signal."""
    client = get_anon_client()
    query = client.table("stocks").select("symbol, company_name, sector, is_nifty50, yf_ticker").eq("active", True)
    if nifty50_only:
        query = query.eq("is_nifty50", True)
    stocks = query.order("symbol").execute().data or []

    # Get latest signals (one per symbol)
    sig_rows = (
        client.table("signals")
        .select("symbol, signal, date")
        .order("date", desc=True)
        .limit(max(50, len(stocks) * 2))
        .execute()
        .data or []
    )
    signal_map = {}
    for row in sig_rows:
        signal_map.setdefault(row["symbol"], row["signal"])

    # Get latest prices from ohlcv (2 rows per symbol for change%)
    symbols = [s["symbol"] for s in stocks]
    price_map: dict[str, dict] = {}
    if symbols:
        ohlcv = (
            client.table("ohlcv")
            .select("symbol, close, date")
            .in_("symbol", symbols)
            .order("date", desc=True)
            .limit(len(symbols) * 2)
            .execute()
            .data or []
        )
        grouped: dict[str, list] = {}
        for row in ohlcv:
            grouped.setdefault(row["symbol"], [])
            if len(grouped[row["symbol"]]) < 2:
                grouped[row["symbol"]].append(row)
        for sym, rows in grouped.items():
            latest = float(rows[0]["close"]) if rows else 0.0
            prev = float(rows[1]["close"]) if len(rows) > 1 else latest
            change_pct = ((latest - prev) / prev * 100) if prev else 0.0
            price_map[sym] = {"price": latest, "change_pct": change_pct}

    enriched = []
    for s in stocks:
        pdata = price_map.get(s["symbol"], {"price": 0.0, "change_pct": 0.0})
        enriched.append({
            "symbol": s["symbol"],
            "company_name": s.get("company_name") or "",
            "sector": s.get("sector") or "",
            "is_nifty50": s.get("is_nifty50", False),
            "price": pdata["price"],
            "change_pct": pdata["change_pct"],
            "signal": signal_map.get(s["symbol"], ""),
        })
    return enriched


def add_stock(symbol: str, access_token: str) -> tuple[bool, str]:
    """Validate a symbol and upsert it into the stocks table."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from services.api.services.market_data import search_instrument
        meta = search_instrument(symbol)
        client = get_authed_client(access_token)
        client.table("stocks").upsert(
            {
                "symbol": symbol.upper(),
                "yf_ticker": meta.instrument_key,
                "active": True,
                "is_nifty50": False,
            },
            on_conflict="symbol",
        ).execute()
        return True, f"{symbol.upper()} added successfully"
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

st.title("Stocks")
st.caption("Indian equity stocks with AI-powered signals")

# Controls row
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 1, 1])
with ctrl1:
    search = st.text_input("🔍 Search symbol or company", placeholder="e.g. RELIANCE, Infosys")
with ctrl2:
    stocks_raw = fetch_stocks()
    sectors = sorted({s["sector"] for s in stocks_raw if s["sector"]})
    sector_filter = st.selectbox("Sector", ["All Sectors"] + sectors)
with ctrl3:
    universe = st.radio("Universe", ["All", "Nifty 50"], horizontal=True)
with ctrl4:
    add_clicked = st.button("➕ Add Stock", use_container_width=True)

# Add stock popover/dialog
if add_clicked:
    st.session_state["show_add_form"] = True

if st.session_state.get("show_add_form"):
    with st.form("add_stock_form"):
        st.markdown("**Add a stock by NSE symbol**")
        new_sym = st.text_input("NSE Symbol (e.g. IRCTC)", key="add_sym")
        c1, c2 = st.columns(2)
        submit = c1.form_submit_button("Add", use_container_width=True)
        cancel = c2.form_submit_button("Cancel", use_container_width=True)
    if cancel:
        st.session_state["show_add_form"] = False
        st.rerun()
    if submit and new_sym.strip():
        with st.spinner(f"Looking up {new_sym.upper()}…"):
            ok, msg = add_stock(new_sym.strip().upper(), get_access_token())
        if ok:
            st.success(msg)
            fetch_stocks.clear()
            st.session_state["show_add_form"] = False
            st.rerun()
        else:
            st.error(f"Failed: {msg}")

# Filter data
nifty_only = universe == "Nifty 50"
stocks = fetch_stocks(nifty_only)

if search:
    q = search.lower()
    stocks = [s for s in stocks if q in s["symbol"].lower() or q in s["company_name"].lower()]
if sector_filter != "All Sectors":
    stocks = [s for s in stocks if s["sector"] == sector_filter]

st.caption(f"Showing {len(stocks)} stocks")

# Table header
hdr = st.columns([2, 4, 3, 2, 2, 2])
hdr[0].markdown("**Symbol**")
hdr[1].markdown("**Company**")
hdr[2].markdown("**Sector**")
hdr[3].markdown("**Price (₹)**")
hdr[4].markdown("**Change %**")
hdr[5].markdown("**Signal**")
st.markdown("<hr style='margin:4px 0 8px'>", unsafe_allow_html=True)

# Rows — clicking navigates to Stock Detail
for stock in stocks:
    row = st.columns([2, 4, 3, 2, 2, 2])
    chg = stock["change_pct"]
    chg_color = "#22c55e" if chg >= 0 else "#ef4444"

    row[0].markdown(f"**{stock['symbol']}**")
    row[1].markdown(stock["company_name"])
    row[2].markdown(f"<span style='color:#94a3b8'>{stock['sector']}</span>", unsafe_allow_html=True)
    row[3].markdown(f"{stock['price']:,.2f}")
    row[4].markdown(
        f"<span style='color:{chg_color}'>{'+' if chg >= 0 else ''}{chg:.2f}%</span>",
        unsafe_allow_html=True,
    )
    if stock["signal"]:
        row[5].markdown(signal_badge_html(stock["signal"]), unsafe_allow_html=True)
    else:
        row[5].markdown("<span style='color:#475569'>—</span>", unsafe_allow_html=True)

    # Invisible button for row click
    with row[0]:
        if st.button("→", key=f"goto_{stock['symbol']}", help=f"View {stock['symbol']}"):
            st.session_state["selected_stock"] = stock["symbol"]
            st.switch_page("pages/3_Stock_Detail.py")

    st.markdown("<hr style='margin:2px 0;border-color:#1e293b'>", unsafe_allow_html=True)
