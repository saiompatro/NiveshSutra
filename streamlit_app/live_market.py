"""Direct market-data helpers for the Streamlit frontend.

This module keeps live prices available even when the FastAPI service URL is
missing or temporarily unavailable. It mirrors the backend's yfinance-based
quote logic so Streamlit can still show current market prices on its own.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf


def _normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    for suffix in (".NS", ".NSE", ".BSE", ".BO"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def _candidate_tickers(symbol: str, preferred_ticker: str | None = None) -> list[str]:
    normalized = _normalize_symbol(symbol)
    preferred = (preferred_ticker or "").strip().upper()
    preferred = preferred.replace(".NSE", ".NS").replace(".BSE", ".BO")

    if preferred:
        return [preferred]
    if normalized in {"^NSEI", "^BSESN"}:
        return [normalized]
    if normalized.endswith((".NS", ".BO")):
        return [normalized]
    return [f"{normalized}.NS", f"{normalized}.BO"]


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_history(provider_symbol: str, days: int = 30) -> pd.DataFrame:
    start = date.today() - timedelta(days=max(days + 10, 20))
    end = date.today() + timedelta(days=1)
    history = yf.Ticker(provider_symbol).history(
        start=start.isoformat(),
        end=end.isoformat(),
        interval="1d",
        auto_adjust=False,
        actions=False,
    )
    if history is None or history.empty:
        return pd.DataFrame()

    history = history.rename(columns=str.lower).reset_index()
    history.columns = [str(column).lower() for column in history.columns]
    index_col = "date" if "date" in history.columns else history.columns[0]
    history["date"] = pd.to_datetime(history[index_col]).dt.strftime("%Y-%m-%d")
    keep_columns = ["date", "open", "high", "low", "close", "volume"]
    for column in keep_columns:
        if column not in history.columns:
            history[column] = 0
    return history[keep_columns].dropna(subset=["close"])


def _safe_fast_info(provider_symbol: str) -> dict[str, Any]:
    try:
        return dict(yf.Ticker(provider_symbol).fast_info or {})
    except Exception:
        return {}


def _quote_from_ticker(provider_symbol: str) -> dict[str, Any]:
    history = _safe_history(provider_symbol, days=10)
    fast_info = _safe_fast_info(provider_symbol)

    if history.empty and not fast_info:
        return {}

    latest = history.iloc[-1].to_dict() if not history.empty else {}
    previous = history.iloc[-2].to_dict() if len(history) > 1 else latest

    previous_close = _coerce_float(
        fast_info.get("previousClose"),
        _coerce_float(fast_info.get("regularMarketPreviousClose"), _coerce_float(previous.get("close"))),
    )
    price = _coerce_float(
        fast_info.get("lastPrice"),
        _coerce_float(fast_info.get("regularMarketPrice"), _coerce_float(latest.get("close"))),
    )
    if not previous_close:
        previous_close = _coerce_float(previous.get("close"), price)

    change = price - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0

    return {
        "provider_symbol": provider_symbol,
        "price": price,
        "previous_close": previous_close,
        "change": change,
        "change_pct": change_pct,
        "open": _coerce_float(fast_info.get("open"), _coerce_float(latest.get("open"), price)),
        "high": _coerce_float(
            fast_info.get("dayHigh"),
            _coerce_float(fast_info.get("regularMarketDayHigh"), _coerce_float(latest.get("high"), price)),
        ),
        "low": _coerce_float(
            fast_info.get("dayLow"),
            _coerce_float(fast_info.get("regularMarketDayLow"), _coerce_float(latest.get("low"), price)),
        ),
        "volume": _coerce_int(
            fast_info.get("lastVolume"),
            _coerce_int(fast_info.get("regularMarketVolume"), _coerce_int(latest.get("volume"))),
        ),
        "latest_trading_day": str(latest.get("date") or datetime.utcnow().strftime("%Y-%m-%d")),
        "provider": "yfinance-direct",
    }


def fetch_live_quotes_batch(requests_map: dict[str, str | None]) -> dict[str, dict[str, Any]]:
    quote_map: dict[str, dict[str, Any]] = {}
    pending: dict[str, str | None] = {symbol: ticker for symbol, ticker in requests_map.items() if symbol}

    for candidate_index in range(2):
        batch_candidates: list[str] = []
        symbol_to_candidate: dict[str, str] = {}

        for symbol, preferred_ticker in pending.items():
            candidates = _candidate_tickers(symbol, preferred_ticker)
            if candidate_index >= len(candidates):
                continue
            candidate = candidates[candidate_index]
            symbol_to_candidate[symbol] = candidate
            batch_candidates.append(candidate)

        if not batch_candidates:
            continue

        resolved_symbols: list[str] = []
        for symbol, candidate in symbol_to_candidate.items():
            quote = _quote_from_ticker(candidate)
            if not quote or not quote.get("price"):
                continue
            quote_map[symbol] = quote
            resolved_symbols.append(symbol)

        for symbol in resolved_symbols:
            pending.pop(symbol, None)

        if not pending:
            break

    return quote_map


def fetch_live_quote(symbol: str, preferred_ticker: str | None = None) -> dict[str, Any]:
    return fetch_live_quotes_batch({symbol: preferred_ticker}).get(symbol, {})


def fetch_historical_daily(symbol: str, preferred_ticker: str | None = None, days: int = 365) -> list[dict[str, Any]]:
    candidates = _candidate_tickers(symbol, preferred_ticker)

    for candidate in candidates:
        history_frame = _safe_history(candidate, days=days)
        history: list[dict[str, Any]] = []
        for _, candle in history_frame.tail(days).iterrows():
            history.append(
                {
                    "date": str(candle["date"]),
                    "open": _coerce_float(candle["open"]),
                    "high": _coerce_float(candle["high"]),
                    "low": _coerce_float(candle["low"]),
                    "close": _coerce_float(candle["close"]),
                    "volume": _coerce_int(candle["volume"]),
                }
            )
        if history:
            return history

    return []
