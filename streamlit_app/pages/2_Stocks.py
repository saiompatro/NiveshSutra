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
from live_market import fetch_live_quotes_batch
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


@st.cache_data(ttl=15, show_spinner=False)
def fetch_stocks(nifty50_only: bool = False) -> list[dict]:
    """Fetch stocks from the live FastAPI market endpoint."""
    try:
        rows = request_json(
            "GET",
            "/api/v1/stocks/live",
            params={"nifty50_only": str(nifty50_only).lower()},
        )
        return [
            {
                "symbol": row["symbol"],
                "company_name": row.get("company_name") or "",
                "sector": row.get("sector") or "",
                "is_nifty50": bool(row.get("is_nifty50", False)),
                "price": float(row.get("current_price") or 0),
                "change_pct": float(row.get("change_pct") or 0),
                "signal": row.get("signal") or "",
                "provider": row.get("provider") or "",
            }
            for row in rows
        ]
    except Exception:
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

        quote_map = fetch_live_quotes_batch({stock["symbol"]: stock.get("yf_ticker") for stock in stocks})

        return [
            {
                "symbol": stock["symbol"],
                "company_name": stock.get("company_name") or "",
                "sector": stock.get("sector") or "",
                "is_nifty50": bool(stock.get("is_nifty50", False)),
                "price": float((quote_map.get(stock["symbol"]) or {}).get("price") or 0),
                "change_pct": float((quote_map.get(stock["symbol"]) or {}).get("change_pct") or 0),
                "signal": signal_map.get(stock["symbol"], ""),
                "provider": (quote_map.get(stock["symbol"]) or {}).get("provider") or "",
            }
            for stock in stocks
        ]


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
    kicker="Stocks",
    title="Browse the equity universe",
    body=f"{len(all_stocks)} tracked names · {len(sectors)} sectors · "
         f"{sum(1 for s in all_stocks if s['is_nifty50'])} Nifty 50",
    pills=[],
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
            change_color = "#343a40" if stock["change_pct"] >= 0 else "#6c757d"
            row[0].markdown(f"**{stock['symbol']}**")
            row[1].markdown(stock["company_name"])
            row[2].markdown(
                f"<span style='color:#6c757d'>{stock['sector'] or 'Unassigned'}</span>",
                unsafe_allow_html=True,
            )
            row[3].markdown(f"{stock['price']:,.2f}")
            row[4].markdown(
                f"<span style='color:{change_color}'>{format_pct(stock['change_pct'])}</span>",
                unsafe_allow_html=True,
            )
            row[5].markdown(
                signal_badge_html(stock["signal"]) if stock["signal"] else "<span style='color:#6c757d'>Waiting</span>",
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
