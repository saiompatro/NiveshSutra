"""Portfolio — holdings table, P&L metrics, allocation pie, MVO optimization."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import plotly.graph_objects as go
from auth import require_auth, get_access_token, get_user_id
from supabase_client import get_anon_client, get_authed_client
from utils import format_currency, format_pct

st.set_page_config(page_title="Portfolio — NiveshSutra", page_icon="💼", layout="wide")
require_auth()

token = get_access_token()
uid = get_user_id()

CHART_COLORS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#06b6d4", "#ec4899", "#f97316", "#14b8a6", "#6366f1",
]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30, show_spinner=False)
def fetch_holdings(user_id: str, access_token: str) -> list:
    rows = (
        get_authed_client(access_token)
        .table("holdings")
        .select("id, symbol, quantity, avg_buy_price")
        .eq("user_id", user_id)
        .execute()
        .data or []
    )
    enriched = []
    for h in rows:
        ohlcv = (
            get_anon_client()
            .table("ohlcv")
            .select("close")
            .eq("symbol", h["symbol"])
            .order("date", desc=True)
            .limit(1)
            .execute()
            .data or []
        )
        price = float(ohlcv[0]["close"]) if ohlcv else float(h["avg_buy_price"])
        qty = float(h["quantity"])
        avg = float(h["avg_buy_price"])
        invested = qty * avg
        value = qty * price
        pnl = value - invested
        pnl_pct = (pnl / invested * 100) if invested else 0.0
        enriched.append({
            "id": h["id"],
            "symbol": h["symbol"],
            "quantity": qty,
            "avg_price": avg,
            "current_price": price,
            "invested": invested,
            "value": value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })
    return enriched


@st.cache_data(ttl=30, show_spinner=False)
def fetch_all_symbols() -> list:
    return (
        get_anon_client()
        .table("stocks")
        .select("symbol, company_name")
        .eq("active", True)
        .order("symbol")
        .execute()
        .data or []
    )


def add_holding(user_id: str, access_token: str, symbol: str, qty: float, avg_price: float):
    get_authed_client(access_token).table("holdings").insert({
        "user_id": user_id,
        "symbol": symbol.upper(),
        "quantity": qty,
        "avg_buy_price": avg_price,
    }).execute()


def delete_holding(holding_id: str, user_id: str, access_token: str):
    get_authed_client(access_token).table("holdings").delete().eq(
        "id", holding_id
    ).eq("user_id", user_id).execute()


def run_optimization(user_id: str, access_token: str, risk_profile: str) -> dict:
    from services.ml.optimizer import run_optimization as _run_opt
    client = get_authed_client(access_token)
    method_map = {"conservative": "min_volatility", "moderate": "max_sharpe", "aggressive": "efficient_return"}
    opt_data = {
        "user_id": user_id,
        "risk_profile": risk_profile,
        "optimization_method": method_map.get(risk_profile, "max_sharpe"),
        "status": "pending",
    }
    result = client.table("portfolio_optimizations").insert(opt_data).execute()
    opt_id = result.data[0]["id"] if result.data else None
    if opt_id:
        return _run_opt(user_id, risk_profile, opt_id)
    return {}


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

with st.spinner("Loading portfolio…"):
    holdings = fetch_holdings(uid, token)
    all_symbols = fetch_all_symbols()

total_invested = sum(h["invested"] for h in holdings)
total_value = sum(h["value"] for h in holdings)
total_pnl = total_value - total_invested
total_pnl_pct = (total_pnl / total_invested * 100) if total_invested else 0.0

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("💼 Portfolio")
st.caption("Manage your holdings and optimise allocation")

hdr_c1, hdr_c2 = st.columns([6, 2])
with hdr_c2:
    add_clicked = st.button("➕ Add Holding", use_container_width=True)
    opt_clicked = st.button(
        "✨ Optimise", use_container_width=True, disabled=len(holdings) == 0
    )

# ---------------------------------------------------------------------------
# Add Holding form
# ---------------------------------------------------------------------------

if add_clicked:
    st.session_state["show_add_holding"] = True

if st.session_state.get("show_add_holding"):
    with st.form("add_holding_form"):
        st.markdown("**Add Holding**")
        symbol_list = [f"{s['symbol']} — {s['company_name']}" for s in all_symbols]
        chosen = st.selectbox("Stock", symbol_list, key="hold_sym")
        chosen_symbol = chosen.split(" — ")[0] if chosen else ""
        qty = st.number_input("Quantity (shares)", min_value=1, step=1)
        avg_price = st.number_input("Average buy price (₹)", min_value=0.01, step=0.01)
        c1, c2 = st.columns(2)
        ok = c1.form_submit_button("Add", use_container_width=True)
        cancel = c2.form_submit_button("Cancel", use_container_width=True)
    if cancel:
        st.session_state["show_add_holding"] = False
        st.rerun()
    if ok and chosen_symbol:
        try:
            add_holding(uid, token, chosen_symbol, float(qty), float(avg_price))
            fetch_holdings.clear()
            st.success(f"{chosen_symbol} added to holdings")
            st.session_state["show_add_holding"] = False
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")

# ---------------------------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------------------------

if holdings:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Value", format_currency(total_value))
    m2.metric("Total Invested", format_currency(total_invested))
    m3.metric(
        "Total P&L",
        format_currency(total_pnl),
        delta=format_pct(total_pnl_pct),
        delta_color="normal",
    )

st.divider()

# ---------------------------------------------------------------------------
# Holdings table
# ---------------------------------------------------------------------------

st.subheader("Holdings")
if not holdings:
    st.info("No holdings yet. Add your first stock above.")
else:
    hdr = st.columns([2, 2, 3, 3, 3, 3, 3, 2])
    for col, label in zip(hdr, ["Symbol", "Qty", "Avg Price", "Current", "P&L", "P&L %", "Value", ""]):
        col.markdown(f"**{label}**")
    st.markdown("<hr style='margin:4px 0 6px;border-color:#334155'>", unsafe_allow_html=True)

    for h in holdings:
        pnl_color = "#22c55e" if h["pnl"] >= 0 else "#ef4444"
        row = st.columns([2, 2, 3, 3, 3, 3, 3, 2])
        row[0].markdown(f"**{h['symbol']}**")
        row[1].markdown(f"{h['quantity']:.0f}")
        row[2].markdown(f"{h['avg_price']:,.2f}")
        row[3].markdown(f"{h['current_price']:,.2f}")
        row[4].markdown(
            f"<span style='color:{pnl_color}'>{format_currency(h['pnl'])}</span>",
            unsafe_allow_html=True,
        )
        row[5].markdown(
            f"<span style='color:{pnl_color}'>{format_pct(h['pnl_pct'])}</span>",
            unsafe_allow_html=True,
        )
        row[6].markdown(format_currency(h["value"]))
        if row[7].button("Remove", key=f"del_{h['id']}"):
            delete_holding(h["id"], uid, token)
            fetch_holdings.clear()
            st.rerun()
        st.markdown("<hr style='margin:3px 0;border-color:#1e293b'>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

if holdings:
    st.divider()
    ch1, ch2 = st.columns(2)

    with ch1:
        st.subheader("Portfolio Allocation")
        fig_pie = go.Figure(go.Pie(
            labels=[h["symbol"] for h in holdings],
            values=[h["value"] for h in holdings],
            hole=0.45,
            marker=dict(colors=CHART_COLORS[:len(holdings)]),
            textinfo="label+percent",
        ))
        fig_pie.update_layout(
            paper_bgcolor="#0f172a", font=dict(color="#f1f5f9"),
            showlegend=False, height=320,
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with ch2:
        st.subheader("P&L by Stock")
        sorted_h = sorted(holdings, key=lambda x: x["pnl"])
        fig_bar = go.Figure(go.Bar(
            x=[h["symbol"] for h in sorted_h],
            y=[h["pnl"] for h in sorted_h],
            marker_color=["#22c55e" if h["pnl"] >= 0 else "#ef4444" for h in sorted_h],
            text=[format_currency(h["pnl"]) for h in sorted_h],
            textposition="outside",
        ))
        fig_bar.update_layout(
            paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
            font=dict(color="#f1f5f9"),
            xaxis=dict(gridcolor="#1e293b"),
            yaxis=dict(gridcolor="#1e293b"),
            height=320, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Portfolio Optimisation
# ---------------------------------------------------------------------------

if opt_clicked and holdings:
    from auth import get_profile
    risk_profile = get_profile().get("risk_profile", "moderate")
    with st.spinner("Running Mean-Variance Optimisation…"):
        try:
            opt = run_optimization(uid, token, risk_profile)
            st.session_state["opt_result"] = opt
        except Exception as e:
            st.error(f"Optimisation failed: {e}")

opt = st.session_state.get("opt_result")
if opt and opt.get("allocations"):
    st.divider()
    st.subheader("✨ Optimisation Results")

    o1, o2, o3 = st.columns(3)
    o1.metric("Expected Annual Return", f"{(opt.get('expected_return', 0) or 0) * 100:.1f}%")
    o2.metric("Annual Volatility", f"{(opt.get('expected_risk', 0) or 0) * 100:.1f}%")
    o3.metric("Sharpe Ratio", f"{opt.get('sharpe_ratio', 0) or 0:.2f}")

    allocs = opt["allocations"]

    oc1, oc2 = st.columns(2)
    with oc1:
        st.markdown("**Recommended Allocation**")
        filtered_allocs = [a for a in allocs if a.get("recommended_weight", 0) > 0.01]
        fig_opt_pie = go.Figure(go.Pie(
            labels=[a["symbol"] for a in filtered_allocs],
            values=[a["recommended_weight"] for a in filtered_allocs],
            hole=0.45,
            marker=dict(colors=CHART_COLORS[:len(filtered_allocs)]),
            textinfo="label+percent",
        ))
        fig_opt_pie.update_layout(
            paper_bgcolor="#0f172a", font=dict(color="#f1f5f9"),
            showlegend=False, height=300, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_opt_pie, use_container_width=True)

    with oc2:
        st.markdown("**Rebalancing Actions**")
        actions = [a for a in allocs if a.get("action") != "hold"]
        actions.sort(key=lambda a: abs(a.get("weight_change", 0)), reverse=True)
        if actions:
            for a in actions:
                action = a.get("action", "")
                color = "#22c55e" if action in ("increase", "buy") else "#ef4444"
                wc = a.get("weight_change", 0) * 100
                curr_w = a.get("current_weight", 0) * 100
                rec_w = a.get("recommended_weight", 0) * 100
                st.markdown(
                    f"<div style='background:#1e293b;border-radius:6px;padding:8px 12px;"
                    f"margin-bottom:6px;display:flex;justify-content:space-between'>"
                    f"<div><strong>{a['symbol']}</strong><br>"
                    f"<span style='font-size:0.75rem;color:#94a3b8'>"
                    f"{curr_w:.1f}% → {rec_w:.1f}%</span></div>"
                    f"<div style='text-align:right'>"
                    f"<strong style='color:{color}'>{action.upper()}</strong><br>"
                    f"<span style='font-size:0.75rem;color:#94a3b8'>"
                    f"{'+' if wc >= 0 else ''}{wc:.1f}%</span></div></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.success("Your portfolio is already well-optimised!")
