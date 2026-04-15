"""
Portfolio optimizer using PyPortfolioOpt.

Supports three risk profiles:
  - conservative -> min_volatility
  - moderate     -> max_sharpe
  - aggressive   -> efficient_return (target = 1.2 * market return)

Falls back to equal-weight allocation on failure.
"""

from __future__ import annotations

import time
import traceback
from typing import Any

import numpy as np
import pandas as pd

from services.ml.config import get_supabase

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RISK_FREE_RATE = 0.07  # ~7% India 10Y govt bond


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_optimization(user_id: str, risk_profile: str, opt_id: str) -> dict[str, Any]:
    """
    Run portfolio optimization for a user.

    Args:
        user_id: UUID of the user.
        risk_profile: One of 'conservative', 'moderate', 'aggressive'.
        opt_id: UUID for this optimization run (pre-created row in
                portfolio_optimizations).

    Returns:
        dict with optimization results.
    """
    sb = get_supabase()
    start = time.time()

    print(
        f"Running optimization for user={user_id}, risk={risk_profile}, opt_id={opt_id}"
    )

    method_map = {
        "conservative": "min_volatility",
        "moderate": "max_sharpe",
        "aggressive": "efficient_return",
    }

    # --- 1. Load user holdings ---
    holdings_resp = (
        sb.table("portfolio_holdings")
        .select("symbol, quantity, avg_cost")
        .eq("user_id", user_id)
        .execute()
    )
    holdings = holdings_resp.data or []
    if not holdings:
        print("No holdings found for user. Returning equal-weight fallback.")
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, [])

    symbols = list({h["symbol"] for h in holdings})
    print(f"  User holds {len(symbols)} symbols: {symbols}")

    # --- 2. Load OHLCV price history (last 365 days) ---
    price_frames: dict[str, pd.Series] = {}
    for sym in symbols:
        resp = (
            sb.table("ohlcv")
            .select("date,close")
            .eq("symbol", sym)
            .order("date", desc=False)
            .limit(365)
            .execute()
        )
        if resp.data and len(resp.data) >= 30:
            df = pd.DataFrame(resp.data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")["close"]
            price_frames[sym] = df

    if len(price_frames) < 2:
        print(
            "Insufficient price data for optimization. Falling back to equal weight."
        )
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, symbols)

    prices_df = pd.DataFrame(price_frames).dropna()
    if len(prices_df) < 30:
        print("Not enough overlapping price data. Falling back to equal weight.")
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, symbols)

    # --- 3. Expected returns & covariance ---
    try:
        from pypfopt import expected_returns, risk_models, EfficientFrontier

        mu = expected_returns.capm_return(prices_df, risk_free_rate=RISK_FREE_RATE)
        cov = risk_models.CovarianceShrinkage(prices_df).ledoit_wolf()

        # --- 4. Optimize ---
        ef = EfficientFrontier(mu, cov)
        method = method_map.get(risk_profile, "max_sharpe")

        if method == "min_volatility":
            ef.min_volatility()
        elif method == "max_sharpe":
            ef.max_sharpe(risk_free_rate=RISK_FREE_RATE)
        elif method == "efficient_return":
            market_return = float(mu.mean())
            target = market_return * 1.2
            ef.efficient_return(target_return=target)

        cleaned = ef.clean_weights()
        perf = ef.portfolio_performance(risk_free_rate=RISK_FREE_RATE)

        expected_return = round(perf[0], 6)
        expected_risk = round(perf[1], 6)
        sharpe_ratio = round(perf[2], 4)

    except Exception as exc:
        print(f"Optimization failed: {exc}")
        traceback.print_exc()
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, symbols)

    # --- 5. Build allocations ---
    total_current_value = 0.0
    current_values: dict[str, float] = {}
    for h in holdings:
        sym = h["symbol"]
        qty = h.get("quantity", 0) or 0
        # Use last close if available, else avg_cost
        if sym in price_frames and len(price_frames[sym]) > 0:
            last_close = float(price_frames[sym].iloc[-1])
            val = qty * last_close
        else:
            val = qty * (h.get("avg_cost", 0) or 0)
        current_values[sym] = val
        total_current_value += val

    allocations: list[dict] = []
    for sym in symbols:
        current_weight = (
            round(current_values.get(sym, 0) / total_current_value, 6)
            if total_current_value > 0
            else 0.0
        )
        recommended_weight = round(cleaned.get(sym, 0.0), 6)
        current_val = round(current_values.get(sym, 0), 2)
        recommended_val = round(recommended_weight * total_current_value, 2)

        allocations.append(
            {
                "optimization_id": opt_id,
                "symbol": sym,
                "current_weight": current_weight,
                "recommended_weight": recommended_weight,
                "current_value": current_val,
                "recommended_value": recommended_val,
            }
        )

    # --- 6. Persist ---
    sb.table("portfolio_optimizations").update(
        {
            "optimization_method": method_map.get(risk_profile, "max_sharpe"),
            "expected_return": expected_return,
            "expected_risk": expected_risk,
            "sharpe_ratio": sharpe_ratio,
            "status": "completed",
        }
    ).eq("id", opt_id).execute()

    if allocations:
        sb.table("optimization_allocations").insert(allocations).execute()

    elapsed = time.time() - start
    print(f"Optimization completed in {elapsed:.1f}s")
    print(f"  Method: {method_map.get(risk_profile)}")
    print(f"  Expected return: {expected_return:.2%}")
    print(f"  Expected risk:   {expected_risk:.2%}")
    print(f"  Sharpe ratio:    {sharpe_ratio:.2f}")

    return {
        "opt_id": opt_id,
        "method": method_map.get(risk_profile),
        "expected_return": expected_return,
        "expected_risk": expected_risk,
        "sharpe_ratio": sharpe_ratio,
        "allocations": allocations,
    }


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


def _equal_weight_fallback(
    sb: Any,
    user_id: str,
    risk_profile: str,
    opt_id: str,
    symbols: list[str],
) -> dict[str, Any]:
    """
    Equal-weight fallback when optimization fails (singular matrix, etc.).
    """
    if not symbols:
        # Get all stocks as default universe
        resp = sb.table("stocks").select("symbol").execute()
        symbols = [r["symbol"] for r in resp.data] if resp.data else []

    n = len(symbols)
    equal_weight = round(1.0 / n, 6) if n > 0 else 0.0

    allocations: list[dict] = []
    for sym in symbols:
        allocations.append(
            {
                "optimization_id": opt_id,
                "symbol": sym,
                "current_weight": 0.0,
                "recommended_weight": equal_weight,
                "current_value": 0.0,
                "recommended_value": 0.0,
            }
        )

    sb.table("portfolio_optimizations").update(
        {
            "optimization_method": "equal_weight_fallback",
            "expected_return": None,
            "expected_risk": None,
            "sharpe_ratio": None,
            "status": "completed_fallback",
        }
    ).eq("id", opt_id).execute()

    if allocations:
        sb.table("optimization_allocations").insert(allocations).execute()

    return {
        "opt_id": opt_id,
        "method": "equal_weight_fallback",
        "expected_return": None,
        "expected_risk": None,
        "sharpe_ratio": None,
        "allocations": allocations,
    }
