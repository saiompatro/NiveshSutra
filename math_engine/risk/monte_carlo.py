from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd


DEFAULT_CONFIDENCE_LEVELS = (0.95, 0.99)
DEFAULT_LOOKBACK_DAYS = 756
DEFAULT_RISK_FREE_RATE = 0.065
MIN_OBSERVATIONS = 60


class MonteCarloRiskError(Exception):
    pass


@dataclass(frozen=True)
class HoldingInput:
    symbol: str
    quantity: float
    avg_buy_price: float


def _normalize_holdings(holdings: Iterable[dict[str, Any]]) -> list[HoldingInput]:
    normalized: list[HoldingInput] = []
    for holding in holdings:
        symbol = str(holding.get("symbol") or "").strip().upper()
        quantity = float(holding.get("quantity") or 0)
        avg_buy_price = float(holding.get("avg_buy_price") or holding.get("avg_price") or 0)
        if symbol and quantity > 0:
            normalized.append(HoldingInput(symbol, quantity, avg_buy_price))
    return normalized


def _price_matrix_from_supabase(
    supabase: Any,
    symbols: list[str],
    lookback_days: int,
) -> pd.DataFrame:
    rows = (
        supabase.table("ohlcv")
        .select("symbol,date,close")
        .in_("symbol", symbols)
        .order("date", desc=True)
        .limit(max(len(symbols) * (lookback_days + 10), len(symbols) * MIN_OBSERVATIONS))
        .execute()
        .data
        or []
    )
    if not rows:
        raise MonteCarloRiskError("No OHLCV rows available for portfolio symbols")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    prices = (
        df.dropna(subset=["close"])
        .pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
        .sort_index()
        .tail(lookback_days)
    )
    prices = prices.dropna(axis=1, thresh=MIN_OBSERVATIONS).ffill().dropna()
    if prices.shape[0] < MIN_OBSERVATIONS or prices.shape[1] == 0:
        raise MonteCarloRiskError("Insufficient overlapping OHLCV history for Monte Carlo risk")
    return prices


def _nearest_psd(matrix: np.ndarray, epsilon: float = 1e-10) -> np.ndarray:
    symmetric = (matrix + matrix.T) * 0.5
    eigvals, eigvecs = np.linalg.eigh(symmetric)
    clipped = np.clip(eigvals, epsilon, None)
    return (eigvecs * clipped) @ eigvecs.T


def _var_cvar(losses: np.ndarray, confidence: float) -> dict[str, float]:
    var = float(np.quantile(losses, confidence, method="linear"))
    tail = losses[losses >= var]
    cvar = float(tail.mean()) if tail.size else var
    return {"var": var, "cvar": cvar}


def run_monte_carlo_var(
    supabase: Any,
    holdings: Iterable[dict[str, Any]],
    *,
    scenarios: int = 10_000,
    horizon_days: int = 1,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    confidence_levels: Iterable[float] = DEFAULT_CONFIDENCE_LEVELS,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    seed: int | None = None,
) -> dict[str, Any]:
    normalized_holdings = _normalize_holdings(holdings)
    if not normalized_holdings:
        raise MonteCarloRiskError("Portfolio has no positive-quantity holdings")

    scenarios = max(10_000, int(scenarios))
    horizon_days = max(1, int(horizon_days))
    lookback_days = max(MIN_OBSERVATIONS, int(lookback_days))
    symbols = sorted({holding.symbol for holding in normalized_holdings})

    prices = _price_matrix_from_supabase(supabase, symbols, lookback_days)
    usable_symbols = list(prices.columns)
    returns = np.log(prices / prices.shift(1)).dropna()
    if returns.shape[0] < MIN_OBSERVATIONS:
        raise MonteCarloRiskError("Not enough return observations after cleaning price history")

    latest_prices = prices.iloc[-1]
    exposures = pd.Series(0.0, index=usable_symbols)
    missing_symbols: list[str] = []
    for holding in normalized_holdings:
        if holding.symbol not in exposures.index:
            missing_symbols.append(holding.symbol)
            continue
        exposures.loc[holding.symbol] += holding.quantity * float(latest_prices.loc[holding.symbol])

    exposures = exposures[exposures > 0]
    if exposures.empty:
        raise MonteCarloRiskError("No holdings have enough price history for risk simulation")

    returns = returns[exposures.index]
    weights = (exposures / exposures.sum()).to_numpy(dtype=float)
    portfolio_value = float(exposures.sum())

    daily_mean = returns.mean().to_numpy(dtype=float)
    daily_cov = returns.cov().to_numpy(dtype=float)
    covariance = _nearest_psd(daily_cov * horizon_days)
    drift = daily_mean * horizon_days

    rng = np.random.default_rng(seed)
    shocks = rng.multivariate_normal(
        mean=drift,
        cov=covariance,
        size=scenarios,
        check_valid="ignore",
    )
    asset_terminal_returns = np.exp(shocks) - 1.0
    portfolio_returns = asset_terminal_returns @ weights
    pnl = portfolio_value * portfolio_returns
    losses = -pnl

    confidence_output: dict[str, dict[str, float]] = {}
    for confidence in confidence_levels:
        confidence = float(confidence)
        risk = _var_cvar(losses, confidence)
        confidence_output[str(int(round(confidence * 100)))] = {
            "var": round(risk["var"], 2),
            "var_pct": round((risk["var"] / portfolio_value) * 100, 4),
            "cvar": round(risk["cvar"], 2),
            "cvar_pct": round((risk["cvar"] / portfolio_value) * 100, 4),
        }

    corr = returns.corr().clip(-1.0, 1.0)
    return {
        "portfolio_value": round(portfolio_value, 2),
        "scenarios": scenarios,
        "horizon_days": horizon_days,
        "lookback_days": int(returns.shape[0]),
        "risk_free_rate": risk_free_rate,
        "symbols": list(exposures.index),
        "dropped_symbols": sorted(set(missing_symbols)),
        "mean_return": round(float(portfolio_returns.mean()), 8),
        "volatility": round(float(portfolio_returns.std(ddof=1)), 8),
        "var": confidence_output,
        "correlation_matrix": {
            symbol: {
                inner_symbol: round(float(value), 6)
                for inner_symbol, value in row.dropna().items()
            }
            for symbol, row in corr.iterrows()
        },
        "methodology": {
            "return_model": "daily log returns from Supabase OHLCV close prices",
            "covariance": "sample covariance with eigenvalue clipping to positive semidefinite",
            "simulation": "vectorized multivariate-normal terminal log-return shocks",
        },
    }
