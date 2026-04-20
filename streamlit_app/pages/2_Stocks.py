"""Stocks page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from api_client import request_json
from auth import get_access_token, get_profile, logout, require_auth
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
from supabase_client import get_anon_client
from utils import format_pct, signal_badge_html

st.set_page_config(page_title="Stocks | NiveshSutra", layout="wide")
apply_theme()
require_auth()


def _render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page="Stocks",
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.switch_page("app.py")


@st.cache_data(ttl=60, show_spinner=False)
def fetch_stocks(nifty50_only: bool = False) -> list[dict]:
    """Fetch stocks with latest close price and signal."""
    client = get_anon_client()
    query = (
        client.table("stocks")
        .select("symbol, company_name, sector, is_nifty50, yf_ticker")
        .eq("active", True)
    )
    if nifty50_only:
        query = query.eq("is_nifty50", True)
    stocks = query.order("symbol").execute().data or []

    signal_rows = (
        client.table("signals")
        .select("symbol, signal, date")
        .order("date", desc=True)
        .limit(max(50, len(stocks) * 2))
        .execute()
        .data
        or []
    )
    signal_map: dict[str, str] = {}
    for row in signal_rows:
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


_render_sidebar()
all_stocks = fetch_stocks()
sectors = sorted({stock["sector"] for stock in all_stocks if stock["sector"]})

render_page_hero(
    kicker="Universe explorer",
    title="Scan the equity field before you commit.",
    body=(
        "This page treats the market like a curated catalog instead of a plain table. Filter by sector, "
        "toggle the benchmark universe, add fresh symbols, and jump into detail pages without losing the atmosphere."
    ),
    pills=["Search across names", "Signal-aware rows", "FastAPI stock onboarding"],
    aside_title="Explorer notes",
    aside_rows=[
        ("Tracked names", str(len(all_stocks))),
        ("Sectors", str(len(sectors))),
        ("Benchmark set", str(sum(1 for stock in all_stocks if stock["is_nifty50"]))),
    ],
)

render_metric_grid(
    [
        {
            "label": "Live universe",
            "value": str(len(all_stocks)),
            "detail": "All active stocks currently available inside the app.",
            "tone": "emerald",
        },
        {
            "label": "Nifty 50",
            "value": str(sum(1 for stock in all_stocks if stock["is_nifty50"])),
            "detail": "Benchmark names are always one toggle away.",
            "tone": "amber",
        },
        {
            "label": "Sector spread",
            "value": str(len(sectors)),
            "detail": "Browse the universe by sector to shift from scanning to thesis-building.",
            "tone": "rose",
        },
    ],
)

render_info_band(
    "Streamlit fit",
    "The explorer keeps native inputs, select boxes, and buttons for reliability, while the surrounding composition gives the page a more magazine-like browsing rhythm.",
)

ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2.2, 1.7, 1.1, 1], gap="medium")
with ctrl1:
    search = st.text_input("Search symbol or company", placeholder="RELIANCE, Infosys, financials...")
with ctrl2:
    sector_filter = st.selectbox("Sector", ["All Sectors"] + sectors)
with ctrl3:
    universe = st.radio("Universe", ["All", "Nifty 50"], horizontal=True)
with ctrl4:
    add_clicked = st.button("Add stock", use_container_width=True)

if add_clicked:
    st.session_state["show_add_form"] = True

if st.session_state.get("show_add_form"):
    with st.form("add_stock_form"):
        render_section_heading(
            "Add a fresh symbol",
            "Use the FastAPI onboarding route to validate and register a stock by NSE symbol.",
            kicker="Onboarding",
        )
        new_symbol = st.text_input("NSE symbol", key="add_symbol", placeholder="IRCTC")
        submit_col, cancel_col = st.columns(2)
        submitted = submit_col.form_submit_button("Add symbol", use_container_width=True)
        cancelled = cancel_col.form_submit_button("Cancel", use_container_width=True)
    if cancelled:
        st.session_state["show_add_form"] = False
        st.rerun()
    if submitted and new_symbol.strip():
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
    lowered = search.lower()
    stocks = [
        stock
        for stock in stocks
        if lowered in stock["symbol"].lower() or lowered in stock["company_name"].lower()
    ]
if sector_filter != "All Sectors":
    stocks = [stock for stock in stocks if stock["sector"] == sector_filter]

positive_count = sum(1 for stock in stocks if stock["change_pct"] >= 0)
signal_count = sum(1 for stock in stocks if stock["signal"])

story_left, story_right = st.columns([1.35, 0.85], gap="large")
with story_left:
    render_section_heading(
        "Filtered tape",
        f"{len(stocks)} names currently match your filters. Open any row to move into the full detail view.",
        kicker="Main catalog",
    )
    if stocks:
        header = st.columns([1.3, 2.8, 2, 1.4, 1.3, 1.5, 0.9], gap="small")
        for column, label in zip(
            header,
            ["Symbol", "Company", "Sector", "Price", "Move", "Signal", ""],
            strict=False,
        ):
            column.markdown(f"**{label}**")
        st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)

        for stock in stocks:
            row = st.columns([1.3, 2.8, 2, 1.4, 1.3, 1.5, 0.9], gap="small")
            change_color = "#5de4c7" if stock["change_pct"] >= 0 else "#ff7f90"
            row[0].markdown(f"**{stock['symbol']}**")
            row[1].markdown(stock["company_name"])
            row[2].markdown(
                f"<span style='color:#9aabc4'>{stock['sector'] or 'Unassigned'}</span>",
                unsafe_allow_html=True,
            )
            row[3].markdown(f"{stock['price']:,.2f}")
            row[4].markdown(
                f"<span style='color:{change_color}'>{format_pct(stock['change_pct'])}</span>",
                unsafe_allow_html=True,
            )
            row[5].markdown(
                signal_badge_html(stock["signal"]) if stock["signal"] else "<span style='color:#6b7a92'>Waiting</span>",
                unsafe_allow_html=True,
            )
            with row[6]:
                if st.button("Open", key=f"open_{stock['symbol']}", use_container_width=True):
                    st.session_state["selected_stock"] = stock["symbol"]
                    st.switch_page("pages/3_Stock_Detail.py")
            st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)
    else:
        render_empty_state("No names match this filter set", "Try broadening the sector or search terms to bring more stocks back into view.")

with story_right:
    render_section_heading(
        "Explorer notes",
        "A quick read on what your current filter set is revealing.",
        kicker="Supporting rail",
    )
    render_note_card(
        "Market breadth",
        "Use the right rail for the meta-story around your filter selection before diving into individual names.",
        rows=[
            ("Matching names", str(len(stocks))),
            ("Positive movers", str(positive_count)),
            ("Rows with signals", str(signal_count)),
        ],
    )
    st.markdown("")
    render_note_card(
        "How the redesign helps",
        "The explorer remains a dependable Streamlit table-and-controls page, but the hero, rail, and metric framing make it feel more like a crafted catalog.",
        rows=[
            ("Inputs", "Native widgets"),
            ("Navigation", "Session-driven detail routing"),
            ("Brand feel", "Editorial layout over utility data"),
        ],
    )
