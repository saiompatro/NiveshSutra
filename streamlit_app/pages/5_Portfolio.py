"""Portfolio page: holdings, PnL, allocation charts, and backend-driven optimization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import plotly.graph_objects as go
import streamlit as st

from api_client import request_json
from auth import get_access_token, get_user_id, require_auth
from supabase_client import get_anon_client, get_authed_client
from utils import format_currency, format_pct

st.set_page_config(page_title="Portfolio - NiveshSutra", page_icon="💼", layout="wide")
require_auth()

token = get_access_token()
uid = get_user_id()

CHART_COLORS = [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#06b6d4",
    "#ec4899",
    "#f97316",
    "#14b8a6",
    "#6366f1",
]


@st.cache_data(ttl=30, show_spinner=False)
def fetch_holdings(user_id: str, access_token: str) -> list[dict]:
    rows = (
        get_authed_client(access_token)
        .table("holdings")
        .select("id, symbol, quantity, avg_buy_price")
        .eq("user_id", user_id)
        .execute()
        .data
        or []
    )
    enriched = []
    for holding in rows:
        ohlcv = (
            get_anon_client()
            .table("ohlcv")
            .select("close")
            .eq("symbol", holding["symbol"])
            .order("date", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        price = float(ohlcv[0]["close"]) if ohlcv else float(holding["avg_buy_price"])
        quantity = float(holding["quantity"])
        avg_price = float(holding["avg_buy_price"])
        invested = quantity * avg_price
        value = quantity * price
        pnl = value - invested
        pnl_pct = (pnl / invested * 100) if invested else 0.0
        enriched.append(
            {
                "id": holding["id"],
                "symbol": holding["symbol"],
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": price,
                "invested": invested,
                "value": value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
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
    get_authed_client(access_token).table("holdings").delete().eq("id", holding_id).eq("user_id", user_id).execute()


def run_optimization(access_token: str) -> dict:
    return request_json(
        "POST",
        "/api/v1/portfolio/optimize",
        access_token=access_token,
        json_body={},
        timeout=120,
    )


with st.spinner("Loading portfolio..."):
    holdings = fetch_holdings(uid, token)
    all_symbols = fetch_all_symbols()

total_invested = sum(holding["invested"] for holding in holdings)
total_value = sum(holding["value"] for holding in holdings)
total_pnl = total_value - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0.0

st.title("Portfolio")
st.caption("Manage your holdings and optimize allocation")

header_left, header_right = st.columns([6, 2])
with header_right:
    add_clicked = st.button("Add Holding", use_container_width=True)
    optimize_clicked = st.button("Optimize", use_container_width=True, disabled=len(holdings) == 0)

if add_clicked:
    st.session_state["show_add_holding"] = True

if st.session_state.get("show_add_holding"):
    with st.form("add_holding_form"):
        st.markdown("**Add Holding**")
        symbol_list = [f"{item['symbol']} - {item['company_name']}" for item in all_symbols]
        chosen = st.selectbox("Stock", symbol_list, key="hold_sym")
        chosen_symbol = chosen.split(" - ")[0] if chosen else ""
        quantity = st.number_input("Quantity (shares)", min_value=1, step=1)
        avg_price = st.number_input("Average buy price (INR)", min_value=0.01, step=0.01)
        c1, c2 = st.columns(2)
        submit = c1.form_submit_button("Add", use_container_width=True)
        cancel = c2.form_submit_button("Cancel", use_container_width=True)
    if cancel:
        st.session_state["show_add_holding"] = False
        st.rerun()
    if submit and chosen_symbol:
        try:
            add_holding(uid, token, chosen_symbol, float(quantity), float(avg_price))
            fetch_holdings.clear()
            st.success(f"{chosen_symbol} added to holdings")
            st.session_state["show_add_holding"] = False
            st.rerun()
        except Exception as exc:
            st.error(f"Failed: {exc}")

if holdings:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Value", format_currency(total_value))
    m2.metric("Total Invested", format_currency(total_invested))
    m3.metric("Total P&L", format_currency(total_pnl), delta=format_pct(total_pnl_pct), delta_color="normal")

st.divider()

st.subheader("Holdings")
if not holdings:
    st.info("No holdings yet. Add your first stock above.")
else:
    table_header = st.columns([2, 2, 3, 3, 3, 3, 3, 2])
    for col, label in zip(
        table_header,
        ["Symbol", "Qty", "Avg Price", "Current", "P&L", "P&L %", "Value", ""],
        strict=False,
    ):
        col.markdown(f"**{label}**")
    st.markdown("<hr style='margin:4px 0 6px;border-color:#334155'>", unsafe_allow_html=True)

    for holding in holdings:
        pnl_color = "#22c55e" if holding["pnl"] >= 0 else "#ef4444"
        row = st.columns([2, 2, 3, 3, 3, 3, 3, 2])
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
        if row[7].button("Remove", key=f"del_{holding['id']}"):
            delete_holding(holding["id"], uid, token)
            fetch_holdings.clear()
            st.rerun()
        st.markdown("<hr style='margin:3px 0;border-color:#1e293b'>", unsafe_allow_html=True)

if holdings:
    st.divider()
    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.subheader("Portfolio Allocation")
        fig_pie = go.Figure(
            go.Pie(
                labels=[holding["symbol"] for holding in holdings],
                values=[holding["value"] for holding in holdings],
                hole=0.45,
                marker=dict(colors=CHART_COLORS[: len(holdings)]),
                textinfo="label+percent",
            )
        )
        fig_pie.update_layout(
            paper_bgcolor="#0f172a",
            font=dict(color="#f1f5f9"),
            showlegend=False,
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with chart_right:
        st.subheader("P&L by Stock")
        sorted_holdings = sorted(holdings, key=lambda item: item["pnl"])
        fig_bar = go.Figure(
            go.Bar(
                x=[holding["symbol"] for holding in sorted_holdings],
                y=[holding["pnl"] for holding in sorted_holdings],
                marker_color=["#22c55e" if holding["pnl"] >= 0 else "#ef4444" for holding in sorted_holdings],
                text=[format_currency(holding["pnl"]) for holding in sorted_holdings],
                textposition="outside",
            )
        )
        fig_bar.update_layout(
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a",
            font=dict(color="#f1f5f9"),
            xaxis=dict(gridcolor="#1e293b"),
            yaxis=dict(gridcolor="#1e293b"),
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

if optimize_clicked and holdings:
    with st.spinner("Running mean-variance optimization..."):
        try:
            optimization = run_optimization(token)
            st.session_state["opt_result"] = optimization
            if optimization.get("status") == "pending":
                st.warning("Optimization request was created, but the backend did not finish computing allocations yet.")
        except Exception as exc:
            st.error(f"Optimization failed: {exc}")

optimization = st.session_state.get("opt_result")
if optimization and optimization.get("allocations"):
    st.divider()
    st.subheader("Optimization Results")

    o1, o2, o3 = st.columns(3)
    o1.metric("Expected Annual Return", f"{(optimization.get('expected_return', 0) or 0) * 100:.1f}%")
    o2.metric("Annual Volatility", f"{(optimization.get('expected_risk', 0) or 0) * 100:.1f}%")
    o3.metric("Sharpe Ratio", f"{optimization.get('sharpe_ratio', 0) or 0:.2f}")

    allocations = optimization["allocations"]
    result_left, result_right = st.columns(2)

    with result_left:
        st.markdown("**Recommended Allocation**")
        filtered_allocations = [allocation for allocation in allocations if allocation.get("recommended_weight", 0) > 0.01]
        fig_opt_pie = go.Figure(
            go.Pie(
                labels=[allocation["symbol"] for allocation in filtered_allocations],
                values=[allocation["recommended_weight"] for allocation in filtered_allocations],
                hole=0.45,
                marker=dict(colors=CHART_COLORS[: len(filtered_allocations)]),
                textinfo="label+percent",
            )
        )
        fig_opt_pie.update_layout(
            paper_bgcolor="#0f172a",
            font=dict(color="#f1f5f9"),
            showlegend=False,
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_opt_pie, use_container_width=True)

    with result_right:
        st.markdown("**Rebalancing Actions**")
        actions = [allocation for allocation in allocations if allocation.get("action") != "hold"]
        actions.sort(key=lambda item: abs(item.get("weight_change", 0)), reverse=True)
        if actions:
            for action_item in actions:
                action = action_item.get("action", "")
                color = "#22c55e" if action in ("increase", "buy") else "#ef4444"
                weight_change = action_item.get("weight_change", 0) * 100
                current_weight = action_item.get("current_weight", 0) * 100
                recommended_weight = action_item.get("recommended_weight", 0) * 100
                st.markdown(
                    f"<div style='background:#1e293b;border-radius:6px;padding:8px 12px;"
                    f"margin-bottom:6px;display:flex;justify-content:space-between'>"
                    f"<div><strong>{action_item['symbol']}</strong><br>"
                    f"<span style='font-size:0.75rem;color:#94a3b8'>"
                    f"{current_weight:.1f}% -> {recommended_weight:.1f}%</span></div>"
                    f"<div style='text-align:right'>"
                    f"<strong style='color:{color}'>{action.upper()}</strong><br>"
                    f"<span style='font-size:0.75rem;color:#94a3b8'>"
                    f"{'+' if weight_change >= 0 else ''}{weight_change:.1f}%</span></div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success("Your portfolio is already well optimized.")
