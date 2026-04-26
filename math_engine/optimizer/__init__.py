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
import zlib

import numpy as np
import pandas as pd

from data.config import get_supabase

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RISK_FREE_RATE = 0.07  # ~7% India 10Y govt bond


def run_optimization(
    user_id: str,
    risk_profile: str,
    opt_id: str,
    supabase: Any | None = None,
) -> dict[str, Any]:
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
    sb = supabase or get_supabase()
    start = time.time()

    print(f"Running optimization for user={user_id}, risk={risk_profile}, opt_id={opt_id}")

    method_map = {
        "conservative": "min_volatility",
        "moderate": "max_sharpe",
        "aggressive": "efficient_return",
    }

    holdings_resp = (
        sb.table("holdings")
        .select("symbol, quantity, avg_buy_price")
        .eq("user_id", user_id)
        .execute()
    )
    holdings = holdings_resp.data or []
    if not holdings:
        print("No holdings found for user. Returning equal-weight fallback.")
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, [])

    symbols = list({h["symbol"] for h in holdings})
    print(f"  User holds {len(symbols)} symbols: {symbols}")

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
        print("Insufficient price data for optimization. Falling back to equal weight.")
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, symbols)

    prices_df = pd.DataFrame(price_frames).dropna()
    if len(prices_df) < 30:
        print("Not enough overlapping price data. Falling back to equal weight.")
        return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, symbols)

    try:
        from pypfopt import expected_returns, risk_models, EfficientFrontier

        mu = expected_returns.capm_return(prices_df, risk_free_rate=RISK_FREE_RATE)
        cov = risk_models.CovarianceShrinkage(prices_df).ledoit_wolf()

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
        print(f"PyPortfolioOpt unavailable or failed: {exc}")
        try:
            cleaned, perf = _vectorized_mean_variance(prices_df, risk_profile, RISK_FREE_RATE)
            expected_return = round(perf[0], 6)
            expected_risk = round(perf[1], 6)
            sharpe_ratio = round(perf[2], 4)
        except Exception as fallback_exc:
            print(f"Vectorized optimizer failed: {fallback_exc}")
            traceback.print_exc()
            return _equal_weight_fallback(sb, user_id, risk_profile, opt_id, symbols)

    total_current_value = 0.0
    current_values: dict[str, float] = {}
    for h in holdings:
        sym = h["symbol"]
        qty = h.get("quantity", 0) or 0
        if sym in price_frames and len(price_frames[sym]) > 0:
            last_close = float(price_frames[sym].iloc[-1])
            val = qty * last_close
        else:
            val = qty * (h.get("avg_buy_price", 0) or 0)
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
                "weight_change": round(recommended_weight - current_weight, 6),
                "action": _rebalance_action(recommended_weight - current_weight),
                "current_value": current_val,
                "recommended_value": recommended_val,
            }
        )

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


def _equal_weight_fallback(
    sb: Any, user_id: str, risk_profile: str, opt_id: str, symbols: list[str]
) -> dict[str, Any]:
    if not symbols:
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
                "weight_change": equal_weight,
                "action": "increase" if equal_weight > 0 else "hold",
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


def _vectorized_mean_variance(
    prices_df: pd.DataFrame,
    risk_profile: str,
    risk_free_rate: float,
) -> tuple[dict[str, float], tuple[float, float, float]]:
    returns = prices_df.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if returns.shape[0] < 30 or returns.shape[1] < 2:
        raise ValueError("not enough return observations")

    symbols = list(returns.columns)
    n_assets = len(symbols)
    daily_mu = returns.mean().to_numpy(dtype=float)
    annual_mu = daily_mu * 252.0
    annual_cov = returns.cov().to_numpy(dtype=float) * 252.0
    annual_cov = np.nan_to_num(annual_cov, nan=0.0, posinf=0.0, neginf=0.0)
    annual_cov = (annual_cov + annual_cov.T) / 2.0
    annual_cov += np.eye(n_assets) * 1e-8

    seed_text = "|".join(symbols) + f"|{risk_profile}"
    rng = np.random.default_rng(zlib.crc32(seed_text.encode("utf-8")))
    sample_count = max(20_000, n_assets * 4_000)
    random_weights = rng.dirichlet(np.ones(n_assets), size=sample_count)

    equal_weight = np.full((1, n_assets), 1.0 / n_assets)
    asset_vol = np.sqrt(np.maximum(np.diag(annual_cov), 1e-12))
    inv_vol = (1.0 / asset_vol)
    inv_vol = (inv_vol / inv_vol.sum()).reshape(1, -1)
    candidates = np.vstack([random_weights, equal_weight, inv_vol])

    portfolio_returns = candidates @ annual_mu
    variances = np.einsum("ij,jk,ik->i", candidates, annual_cov, candidates)
    portfolio_risks = np.sqrt(np.maximum(variances, 1e-12))
    sharpes = (portfolio_returns - risk_free_rate) / portfolio_risks

    if risk_profile == "conservative":
        best_idx = int(np.argmin(portfolio_risks))
    elif risk_profile == "aggressive":
        target_return = max(float(np.mean(annual_mu)) * 1.2, risk_free_rate)
        feasible = np.flatnonzero(portfolio_returns >= target_return)
        best_idx = int(feasible[np.argmin(portfolio_risks[feasible])]) if len(feasible) else int(np.argmax(portfolio_returns))
    else:
        best_idx = int(np.argmax(sharpes))

    weights = candidates[best_idx]
    weights = np.where(weights < 1e-4, 0.0, weights)
    weights = weights / weights.sum() if weights.sum() else np.full(n_assets, 1.0 / n_assets)

    expected_return = float(weights @ annual_mu)
    expected_risk = float(np.sqrt(max(weights @ annual_cov @ weights, 1e-12)))
    sharpe_ratio = float((expected_return - risk_free_rate) / expected_risk)
    cleaned = {symbol: round(float(weight), 6) for symbol, weight in zip(symbols, weights, strict=False)}
    return cleaned, (expected_return, expected_risk, sharpe_ratio)


def _rebalance_action(weight_change: float) -> str:
    if weight_change > 0.01:
        return "increase"
    if weight_change < -0.01:
        return "decrease"
    return "hold"
