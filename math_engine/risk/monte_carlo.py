from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable

import numpy as np
import pandas as pd

try:  # SciPy is preferred for low-discrepancy sequences, but the engine still works without it.
    from scipy.stats import norm, qmc
except Exception:  # pragma: no cover - exercised only in minimal deployments
    norm = None
    qmc = None


DEFAULT_CONFIDENCE_LEVELS = (0.95, 0.99)
DEFAULT_LOOKBACK_DAYS = 756
DEFAULT_RISK_FREE_RATE = 0.065
DEFAULT_SAMPLING_METHOD = "auto"
DEFAULT_IMPORTANCE_SAMPLING = True
DEFAULT_IMPORTANCE_SHIFT = 1.25
MIN_OBSERVATIONS = 60
_EPSILON = 1e-12


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
    psd = (eigvecs * clipped) @ eigvecs.T
    return (psd + psd.T) * 0.5


def _stable_cholesky(matrix: np.ndarray, max_attempts: int = 5) -> np.ndarray:
    diagonal_jitter = 1e-12
    identity = np.eye(matrix.shape[0], dtype=np.float64)
    for _ in range(max_attempts):
        try:
            return np.linalg.cholesky(matrix + identity * diagonal_jitter)
        except np.linalg.LinAlgError:
            diagonal_jitter *= 10.0
    return np.linalg.cholesky(_nearest_psd(matrix, epsilon=diagonal_jitter))


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.dot(values, weights))


def _weighted_std(values: np.ndarray, weights: np.ndarray, mean: float) -> float:
    variance = float(np.dot((values - mean) ** 2, weights))
    return math.sqrt(max(variance, 0.0))


def _weighted_var_cvar(losses: np.ndarray, weights: np.ndarray, confidence: float) -> dict[str, float]:
    order = np.argsort(losses, kind="mergesort")
    sorted_losses = losses[order]
    sorted_weights = weights[order]
    cumulative_weights = np.cumsum(sorted_weights)
    var_index = int(np.searchsorted(cumulative_weights, confidence, side="left"))
    var_index = min(var_index, sorted_losses.size - 1)
    var = float(sorted_losses[var_index])

    tail_mask = sorted_losses >= var
    tail_weights = sorted_weights[tail_mask]
    tail_weight_sum = float(tail_weights.sum())
    if tail_weight_sum <= 0.0:
        cvar = var
    else:
        cvar = float(np.dot(sorted_losses[tail_mask], tail_weights) / tail_weight_sum)
    return {"var": var, "cvar": cvar}


def _normal_from_low_discrepancy(
    scenarios: int,
    dimensions: int,
    *,
    seed: int | None,
    method: str,
) -> tuple[np.ndarray, str]:
    if qmc is None or norm is None:
        raise MonteCarloRiskError("SciPy QMC is unavailable")

    if method == "halton":
        sampler = qmc.Halton(d=dimensions, scramble=True, seed=seed)
        uniforms = sampler.random(scenarios)
        actual_method = "halton_qmc"
    else:
        sampler = qmc.Sobol(d=dimensions, scramble=True, seed=seed)
        power = math.ceil(math.log2(scenarios))
        if 2**power == scenarios:
            uniforms = sampler.random_base2(power)
        else:
            uniforms = sampler.random(scenarios)
        actual_method = "sobol_qmc"

    uniforms = np.clip(uniforms, _EPSILON, 1.0 - _EPSILON)
    return norm.ppf(uniforms).astype(np.float64, copy=False), actual_method


def _normal_from_antithetic(
    scenarios: int,
    dimensions: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, str]:
    half = (scenarios + 1) // 2
    base = rng.standard_normal((half, dimensions), dtype=np.float64)
    normals = np.empty((half * 2, dimensions), dtype=np.float64)
    normals[:half] = base
    normals[half:] = -base
    return normals[:scenarios], "pseudo_random_antithetic"


def _standard_normal_scenarios(
    scenarios: int,
    dimensions: int,
    *,
    seed: int | None,
    method: str,
) -> tuple[np.ndarray, str]:
    method = (method or DEFAULT_SAMPLING_METHOD).strip().lower()
    if method not in {"auto", "sobol", "halton", "pseudo_random", "antithetic"}:
        raise MonteCarloRiskError(f"Unsupported sampling method: {method}")

    if method in {"auto", "sobol", "halton"}:
        try:
            qmc_method = "sobol" if method == "auto" else method
            return _normal_from_low_discrepancy(scenarios, dimensions, seed=seed, method=qmc_method)
        except Exception:
            if method != "auto":
                raise

    rng = np.random.default_rng(seed)
    if method == "pseudo_random":
        return rng.standard_normal((scenarios, dimensions), dtype=np.float64), "pseudo_random"
    return _normal_from_antithetic(scenarios, dimensions, rng)


def _importance_direction(cholesky: np.ndarray, weights: np.ndarray) -> np.ndarray:
    direction = -(cholesky.T @ weights)
    norm_value = float(np.linalg.norm(direction))
    if norm_value <= _EPSILON:
        return np.zeros_like(direction)
    return direction / norm_value


def _likelihood_weights(shifted_normals: np.ndarray, theta: np.ndarray) -> np.ndarray:
    theta_norm_sq = float(theta @ theta)
    log_weights = -(shifted_normals @ theta) + 0.5 * theta_norm_sq
    log_weights -= float(np.max(log_weights))
    weights = np.exp(log_weights).astype(np.float64, copy=False)
    total = float(weights.sum())
    if not np.isfinite(total) or total <= 0.0:
        raise MonteCarloRiskError("Importance sampling weights became numerically unstable")
    return weights / total


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
    sampling_method: str = DEFAULT_SAMPLING_METHOD,
    importance_sampling: bool = DEFAULT_IMPORTANCE_SAMPLING,
    importance_shift: float = DEFAULT_IMPORTANCE_SHIFT,
) -> dict[str, Any]:
    normalized_holdings = _normalize_holdings(holdings)
    if not normalized_holdings:
        raise MonteCarloRiskError("Portfolio has no positive-quantity holdings")

    scenarios = min(max(1_000, int(scenarios)), 50_000)
    horizon_days = min(max(1, int(horizon_days)), 30)
    lookback_days = min(max(MIN_OBSERVATIONS, int(lookback_days)), 1_260)
    requested_sampling_method = (sampling_method or DEFAULT_SAMPLING_METHOD).strip().lower()
    if requested_sampling_method in {"auto", "sobol"} and qmc is not None and norm is not None:
        scenarios = 1 << math.ceil(math.log2(scenarios))
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
    cholesky = _stable_cholesky(covariance)

    normals, actual_sampling_method = _standard_normal_scenarios(
        scenarios,
        len(weights),
        seed=seed,
        method=sampling_method,
    )
    theta = np.zeros(len(weights), dtype=np.float64)
    sample_weights = np.full(scenarios, 1.0 / scenarios, dtype=np.float64)
    if importance_sampling:
        theta = _importance_direction(cholesky, weights) * max(0.0, float(importance_shift))
        if np.any(theta):
            normals += theta
            sample_weights = _likelihood_weights(normals, theta)

    shocks = normals @ cholesky.T
    shocks += drift
    np.expm1(shocks, out=shocks)
    portfolio_returns = shocks @ weights
    losses = -(portfolio_value * portfolio_returns)

    confidence_output: dict[str, dict[str, float]] = {}
    for confidence in confidence_levels:
        confidence = float(confidence)
        if not 0.0 < confidence < 1.0:
            raise MonteCarloRiskError(f"Confidence level must be between 0 and 1: {confidence}")
        risk = _weighted_var_cvar(losses, sample_weights, confidence)
        confidence_output[str(int(round(confidence * 100)))] = {
            "var": round(risk["var"], 2),
            "var_pct": round((risk["var"] / portfolio_value) * 100, 4),
            "cvar": round(risk["cvar"], 2),
            "cvar_pct": round((risk["cvar"] / portfolio_value) * 100, 4),
        }

    weighted_return_mean = _weighted_mean(portfolio_returns, sample_weights)
    weighted_return_std = _weighted_std(portfolio_returns, sample_weights, weighted_return_mean)
    corr = returns.corr().clip(-1.0, 1.0)
    return {
        "portfolio_value": round(portfolio_value, 2),
        "scenarios": scenarios,
        "horizon_days": horizon_days,
        "lookback_days": int(returns.shape[0]),
        "risk_free_rate": risk_free_rate,
        "symbols": list(exposures.index),
        "dropped_symbols": sorted(set(missing_symbols)),
        "mean_return": round(weighted_return_mean, 8),
        "volatility": round(weighted_return_std, 8),
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
            "sampling": actual_sampling_method,
            "importance_sampling": bool(importance_sampling and np.any(theta)),
            "importance_shift": round(float(np.linalg.norm(theta)), 6),
            "simulation": "vectorized low-discrepancy normal shocks, Cholesky factorization, and weighted tail estimation",
        },
    }
