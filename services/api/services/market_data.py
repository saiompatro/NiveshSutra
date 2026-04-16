from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import threading
import time
from typing import Any

import httpx
from supabase import Client

from ..config import get_settings


BASE_URL = "https://www.alphavantage.co/query"
DEFAULT_CACHE_TTL_SECONDS = 60


class MarketDataError(Exception):
    pass


@dataclass
class QuoteSnapshot:
    provider_symbol: str
    price: float
    previous_close: float
    change: float
    change_pct: float
    open: float
    high: float
    low: float
    volume: int
    latest_trading_day: str
    provider: str = "alpha_vantage"


_cache_lock = threading.Lock()
_quote_cache: dict[str, tuple[float, QuoteSnapshot]] = {}
_provider_backoff_until = 0.0


def _cache_ttl_seconds() -> int:
    settings = get_settings()
    ttl = getattr(settings, "market_data_cache_ttl_seconds", DEFAULT_CACHE_TTL_SECONDS)
    return max(10, ttl)


def _cache_key(symbol: str) -> str:
    return symbol.strip().upper()


def _from_cache(symbol: str) -> QuoteSnapshot | None:
    key = _cache_key(symbol)
    with _cache_lock:
        cached = _quote_cache.get(key)
        if not cached:
            return None
        cached_at, quote = cached
        if time.time() - cached_at > _cache_ttl_seconds():
            _quote_cache.pop(key, None)
            return None
        return quote


def _store_cache(symbol: str, quote: QuoteSnapshot) -> QuoteSnapshot:
    with _cache_lock:
        _quote_cache[_cache_key(symbol)] = (time.time(), quote)
    return quote


def _alpha_vantage_candidates(symbol: str) -> list[str]:
    normalized = symbol.strip().upper()
    if normalized == "^NSEI":
        return ["NIFTY.BSE", "^NSEI"]
    if "." in normalized:
        return [normalized]
    return [f"{normalized}.BSE", f"{normalized}.NSE", normalized]


def _is_rate_limited(payload: dict[str, Any]) -> bool:
    info = str(payload.get("Information") or payload.get("Note") or "")
    return "premium" in info.lower() or "request" in info.lower() or "using alpha vantage" in info.lower()


def fetch_live_quote(symbol: str) -> QuoteSnapshot:
    cached = _from_cache(symbol)
    if cached:
        return cached

    global _provider_backoff_until
    if time.time() < _provider_backoff_until:
        raise MarketDataError("Alpha Vantage is temporarily cooling down after a rate limit")

    settings = get_settings()
    if not settings.alpha_vantage_api_key:
        raise MarketDataError("Alpha Vantage API key is not configured")

    last_error = "No live quote found"
    with httpx.Client(timeout=15.0) as client:
        for candidate in _alpha_vantage_candidates(symbol):
            response = client.get(
                BASE_URL,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": candidate,
                    "apikey": settings.alpha_vantage_api_key,
                },
            )
            payload = response.json()
            if _is_rate_limited(payload):
                _provider_backoff_until = time.time() + 300
                raise MarketDataError(payload.get("Information") or payload.get("Note") or "Alpha Vantage rate limit reached")

            quote = payload.get("Global Quote") or {}
            if not quote or not quote.get("05. price"):
                last_error = f"No quote for {candidate}"
                continue

            previous_close = float(quote.get("08. previous close", 0) or 0)
            change = float(quote.get("09. change", 0) or 0)
            price = float(quote.get("05. price", 0) or 0)
            change_pct_raw = str(quote.get("10. change percent", "0")).replace("%", "")
            return _store_cache(
                symbol,
                QuoteSnapshot(
                    provider_symbol=str(quote.get("01. symbol") or candidate),
                    open=float(quote.get("02. open", 0) or 0),
                    high=float(quote.get("03. high", 0) or 0),
                    low=float(quote.get("04. low", 0) or 0),
                    price=price,
                    volume=int(float(quote.get("06. volume", 0) or 0)),
                    latest_trading_day=str(quote.get("07. latest trading day") or ""),
                    previous_close=previous_close,
                    change=change if change else price - previous_close,
                    change_pct=float(change_pct_raw or 0),
                ),
            )

    raise MarketDataError(last_error)


def get_latest_db_bar(supabase: Client, symbol: str) -> dict[str, Any] | None:
    result = (
        supabase.table("ohlcv")
        .select("date, open, high, low, close, volume")
        .eq("symbol", symbol)
        .order("date", desc=True)
        .limit(2)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def get_latest_db_bars(supabase: Client, symbols: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not symbols:
        return {}
    result = (
        supabase.table("ohlcv")
        .select("symbol, date, open, high, low, close, volume")
        .in_("symbol", symbols)
        .order("date", desc=True)
        .limit(max(2, len(symbols) * 3))
        .execute()
    )
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in result.data or []:
        grouped.setdefault(row["symbol"], [])
        if len(grouped[row["symbol"]]) < 2:
            grouped[row["symbol"]].append(row)
    return grouped


def get_quote_with_fallback(supabase: Client, symbol: str) -> QuoteSnapshot:
    try:
        return fetch_live_quote(symbol)
    except Exception:
        rows = get_latest_db_bars(supabase, [symbol]).get(symbol, [])
        if not rows:
            raise

        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else latest
        previous_close = float(previous.get("close", latest.get("close", 0)) or 0)
        price = float(latest.get("close", 0) or 0)
        change = price - previous_close
        change_pct = (change / previous_close * 100) if previous_close else 0.0
        return QuoteSnapshot(
            provider_symbol=symbol,
            price=price,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            open=float(latest.get("open", 0) or 0),
            high=float(latest.get("high", 0) or 0),
            low=float(latest.get("low", 0) or 0),
            volume=int(latest.get("volume", 0) or 0),
            latest_trading_day=str(latest.get("date") or ""),
            provider="supabase",
        )


def merge_live_quote_into_history(history: list[dict[str, Any]], quote: QuoteSnapshot) -> list[dict[str, Any]]:
    if not history:
        return history

    merged = [dict(item) for item in history]
    target_day = quote.latest_trading_day or str(date.today())
    live_bar = {
        "date": target_day,
        "open": quote.open or merged[-1]["open"],
        "high": max(float(merged[-1]["high"]), quote.high or quote.price),
        "low": min(float(merged[-1]["low"]), quote.low or quote.price),
        "close": quote.price,
        "volume": quote.volume or merged[-1]["volume"],
    }

    if merged[-1]["date"] == target_day:
        merged[-1] = {**merged[-1], **live_bar}
    elif merged[-1]["date"] < target_day:
        merged.append(live_bar)
    return merged
