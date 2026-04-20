"""Portfolio page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.graph_objects as go
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
    style_plotly_figure,
)
from live_market import fetch_live_quotes_batch
from supabase_client import get_anon_client, get_authed_client
from utils import format_currency, format_pct

st.set_page_config(page_title="Portfolio | NiveshSutra", layout="wide")
apply_theme()
require_auth()

CHART_COLORS = [
    "#7bc8ff",
    "#5de4c7",
    "#f3a45c",
    "#ff7f90",
    "#86a8ff",
    "#ffd580",
    "#a7f3d0",
    "#ffb4a2",
]


def _render_sidebar() -> None:
    profile = get_profile()
    render_sidebar_shell(
        active_page="Portfolio",
        user_email=st.session_state["user"].email,
        risk_profile=profile.get("risk_profile"),
        headline="Turn holdings into an allocation story: current exposure, live PnL, and optimizer suggestions in one studio.",
    )
    with st.sidebar:
        st.markdown("")
        if st.button("Sign out", use_container_width=True):
            logout()
            st.switch_page("app.py")


@st.cache_data(ttl=15, show_spinner=False)
def fetch_holdings(user_id: str, access_token: str) -> list[dict]:
    try:
        rows = request_json(
            "GET",
            "/api/v1/holdings/live",
            access_token=access_token,
        )
        enriched = []
        for holding in rows:
            quantity = float(holding["quantity"])
            average_price = float(holding["avg_price"])
            current_price = float(holding["current_price"])
            invested = quantity * average_price
            value = float(holding["value"])
            pnl = float(holding["pnl"])
            pnl_pct = float(holding["pnl_pct"])
            enriched.append(
                {
                    "id": holding["id"],
                    "symbol": holding["symbol"],
                    "quantity": quantity,
                    "avg_price": average_price,
                    "current_price": current_price,
                    "invested": invested,
                    "value": value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "provider": holding.get("provider") or "",
                }
            )
        return enriched
    except Exception:
        rows = (
            get_authed_client(access_token)
            .table("holdings")
            .select("id, symbol, quantity, avg_buy_price, stocks(yf_ticker)")
            .eq("user_id", user_id)
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
        enriched = []
        for holding in rows:
            quantity = float(holding["quantity"])
            average_price = float(holding["avg_buy_price"])
            quote = quote_map.get(holding["symbol"]) or {}
            current_price = float(quote.get("price") or average_price)
            invested = quantity * average_price
            value = quantity * current_price
            pnl = value - invested
            pnl_pct = (pnl / invested * 100) if invested else 0.0
            enriched.append(
                {
                    "id": holding["id"],
                    "symbol": holding["symbol"],
                    "quantity": quantity,
                    "avg_price": average_price,
                    "current_price": current_price,
                    "invested": invested,
                    "value": value,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "provider": quote.get("provider") or "",
                }
            )
        return enriched


@st.cache_data(ttl=30, show_spinner=False)
def fetch_all_symbols() -> list[dict]:
    return (
        get_anon_client()
        .table("stocks")
        .select("symbol, company_name")
        .eq("active", True)
        .order("symbol")
        .execute()
        .data
        or []
    )


def add_holding(user_id: str, access_token: str, symbol: str, quantity: float, avg_price: float) -> None:
    get_authed_client(access_token).table("holdings").insert(
        {
            "user_id": user_id,
            "symbol": symbol.upper(),
            "quantity": quantity,
            "avg_buy_price": avg_price,
        }
    ).execute()


def delete_holding(holding_id: str, user_id: str, access_token: str) -> None:
    get_authed_client(access_token).table("holdings").delete().eq("id", holding_id).eq(
        "user_id", user_id
    ).execute()


def run_optimization(access_token: str) -> dict:
    return request_json(
        "POST",
        "/api/v1/portfolio/optimize",
        access_token=access_token,
        json_body={},
        timeout=120,
    )


_render_sidebar()
token = get_access_token()
user_id = get_user_id()

with st.spinner("Loading portfolio..."):
    holdings = fetch_holdings(user_id, token)
    all_symbols = fetch_all_symbols()

total_invested = sum(item["invested"] for item in holdings)
total_value = sum(item["value"] for item in holdings)
total_pnl = total_value - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0.0

render_page_hero(
    kicker="Allocation studio",
    title="Shape the portfolio, not just the positions.",
    body=(
        "This surface treats holdings as a composition problem: current exposure, live PnL, allocation balance, and rebalancing opportunities all share the same visual rhythm."
    ),
    pills=[
        f"Holdings: {len(holdings)}",
        f"Value: {format_currency(total_value)}",
        f"PnL: {format_pct(total_pnl_pct)}",
    ],
    aside_title="Current posture",
    aside_rows=[
        ("Invested capital", format_currency(total_invested)),
        ("Current value", format_currency(total_value)),
        ("Net PnL", format_currency(total_pnl)),
    ],
)

render_metric_grid(
    [
        {
            "label": "Portfolio value",
            "value": format_currency(total_value),
            "detail": "Current marked-to-market value across all holdings.",
            "tone": "emerald",
        },
        {
            "label": "Capital deployed",
            "value": format_currency(total_invested),
            "detail": "Total invested cost basis across the portfolio.",
            "tone": "amber",
        },
        {
            "label": "Net PnL",
            "value": format_currency(total_pnl),
            "detail": format_pct(total_pnl_pct),
            "tone": "emerald" if total_pnl >= 0 else "rose",
        },
    ],
)

render_info_band(
    "Design logic",
    "Portfolio is often where Streamlit apps collapse into card clutter. This redesign keeps the controls native, but uses a single narrative arc: holdings first, allocation second, optimization third.",
)

action_col, action_col_2 = st.columns([1, 1], gap="medium")
add_clicked = action_col.button("Add holding", use_container_width=True)
optimize_clicked = action_col_2.button(
    "Run optimizer",
    use_container_width=True,
    disabled=not holdings,
)

if add_clicked:
    st.session_state["show_add_holding"] = True

if st.session_state.get("show_add_holding"):
    with st.form("add_holding_form"):
        render_section_heading(
            "Add a holding",
            "Translate a signal or an external position into the portfolio store.",
            kicker="Input",
        )
        symbol_list = [f"{item['symbol']} - {item['company_name']}" for item in all_symbols]
        chosen = st.selectbox("Stock", symbol_list, key="holding_symbol")
        chosen_symbol = chosen.split(" - ")[0] if chosen else ""
        quantity = st.number_input("Quantity", min_value=1, step=1)
        avg_price = st.number_input("Average buy price", min_value=0.01, step=0.01)
        submit_col, cancel_col = st.columns(2, gap="medium")
        submitted = submit_col.form_submit_button("Add holding", use_container_width=True)
        cancelled = cancel_col.form_submit_button("Cancel", use_container_width=True)
    if cancelled:
        st.session_state["show_add_holding"] = False
        st.rerun()
    if submitted and chosen_symbol:
        try:
            add_holding(user_id, token, chosen_symbol, float(quantity), float(avg_price))
            fetch_holdings.clear()
            st.session_state["show_add_holding"] = False
            st.success(f"{chosen_symbol} added to your portfolio.")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed: {exc}")

render_section_heading(
    "Holdings ledger",
    "This stays dense and operational, but the framing keeps it from feeling like a plain spreadsheet.",
    kicker="Primary lane",
)

if holdings:
    header = st.columns([1.2, 1, 1.3, 1.3, 1.2, 1.2, 1.3, 1], gap="small")
    for column, label in zip(
        header,
        ["Symbol", "Qty", "Avg price", "Current", "PnL", "PnL %", "Value", ""],
        strict=False,
    ):
        column.markdown(f"**{label}**")
    st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)

    for holding in holdings:
        pnl_color = "#5de4c7" if holding["pnl"] >= 0 else "#ff7f90"
        row = st.columns([1.2, 1, 1.3, 1.3, 1.2, 1.2, 1.3, 1], gap="small")
        row[0].markdown(f"**{holding['symbol']}**")
        row[1].markdown(f"{holding['quantity']:.0f}")
        row[2].markdown(f"{holding['avg_price']:,.2f}")
        row[3].markdown(f"{holding['current_price']:,.2f}")
        row[4].markdown(
            f"<span style='color:{pnl_color}'>{format_currency(holding['pnl'])}</span>",
            unsafe_allow_html=True,
        )
        row[5].markdown(
            f"<span style='color:{pnl_color}'>{format_pct(holding['pnl_pct'])}</span>",
            unsafe_allow_html=True,
        )
        row[6].markdown(format_currency(holding["value"]))
        with row[7]:
            if st.button("Remove", key=f"remove_{holding['id']}", use_container_width=True):
                delete_holding(holding["id"], user_id, token)
                fetch_holdings.clear()
                st.rerun()
        st.markdown('<div class="ns-row-divider"></div>', unsafe_allow_html=True)
else:
    render_empty_state("No holdings yet", "Add your first stock above to unlock allocation and optimization views.")

if holdings:
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        render_section_heading(
            "Allocation shape",
            "A visual read of how much capital each position currently carries.",
            kicker="Chart lane",
        )
        fig_pie = go.Figure(
            go.Pie(
                labels=[holding["symbol"] for holding in holdings],
                values=[holding["value"] for holding in holdings],
                hole=0.48,
                marker=dict(colors=CHART_COLORS[: len(holdings)]),
                textinfo="label+percent",
            )
        )
        st.plotly_chart(style_plotly_figure(fig_pie, height=340), use_container_width=True)

    with chart_right:
        render_section_heading(
            "PnL distribution",
            "A quick way to see which positions are driving the portfolio mood.",
            kicker="Chart lane",
        )
        sorted_holdings = sorted(holdings, key=lambda item: item["pnl"])
        fig_bar = go.Figure(
            go.Bar(
                x=[holding["symbol"] for holding in sorted_holdings],
                y=[holding["pnl"] for holding in sorted_holdings],
                marker_color=[
                    "#5de4c7" if holding["pnl"] >= 0 else "#ff7f90" for holding in sorted_holdings
                ],
                text=[format_currency(holding["pnl"]) for holding in sorted_holdings],
                textposition="outside",
            )
        )
        st.plotly_chart(style_plotly_figure(fig_bar, height=340), use_container_width=True)

if optimize_clicked and holdings:
    with st.spinner("Running mean-variance optimization..."):
        try:
            optimization = run_optimization(token)
            st.session_state["opt_result"] = optimization
            if optimization.get("status") == "pending":
                st.warning("Optimization request was created, but the backend has not finished computing allocations yet.")
        except Exception as exc:
            st.error(f"Optimization failed: {exc}")

optimization = st.session_state.get("opt_result")
if optimization and optimization.get("allocations"):
    render_section_heading(
        "Optimizer output",
        "The final scene translates portfolio math into weight changes and rebalancing moves.",
        kicker="Optimization",
    )
    render_metric_grid(
        [
            {
                "label": "Expected return",
                "value": f"{(optimization.get('expected_return', 0) or 0) * 100:.1f}%",
                "detail": "Projected annualized return from the optimizer.",
                "tone": "emerald",
            },
            {
                "label": "Expected volatility",
                "value": f"{(optimization.get('expected_risk', 0) or 0) * 100:.1f}%",
                "detail": "Annualized risk estimate based on optimizer inputs.",
                "tone": "amber",
            },
            {
                "label": "Sharpe ratio",
                "value": f"{optimization.get('sharpe_ratio', 0) or 0:.2f}",
                "detail": "Risk-adjusted efficiency of the proposed allocation.",
                "tone": "rose",
            },
        ]
    )

    allocations = optimization["allocations"]
    left_col, right_col = st.columns([1.05, 0.95], gap="large")
    with left_col:
        filtered_allocations = [
            item for item in allocations if item.get("recommended_weight", 0) > 0.01
        ]
        fig_opt = go.Figure(
            go.Pie(
                labels=[item["symbol"] for item in filtered_allocations],
                values=[item["recommended_weight"] for item in filtered_allocations],
                hole=0.48,
                marker=dict(colors=CHART_COLORS[: len(filtered_allocations)]),
                textinfo="label+percent",
            )
        )
        st.plotly_chart(style_plotly_figure(fig_opt, height=320), use_container_width=True)

    with right_col:
        actions = [item for item in allocations if item.get("action") != "hold"]
        actions.sort(key=lambda item: abs(item.get("weight_change", 0)), reverse=True)
        if actions:
            for action in actions:
                direction = action.get("action", "")
                color = "#5de4c7" if direction in {"increase", "buy"} else "#ff7f90"
                render_note_card(
                    action["symbol"],
                    f"{direction.upper()} from {action.get('current_weight', 0) * 100:.1f}% to {action.get('recommended_weight', 0) * 100:.1f}% target weight.",
                    rows=[("Weight change", f"{action.get('weight_change', 0) * 100:+.1f}%")],
                )
                st.markdown(
                    f"<div style='height:4px;border-radius:999px;background:{color};opacity:0.6;margin:-0.4rem 0 1rem;'></div>",
                    unsafe_allow_html=True,
                )
        else:
            render_note_card(
                "Already balanced",
                "The optimizer is not recommending any major action right now.",
            )
