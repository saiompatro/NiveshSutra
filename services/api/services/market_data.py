from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import threading
import time
from typing import Any
from urllib.parse import quote

import httpx
from supabase import Client

from ..config import get_settings


DEFAULT_CACHE_TTL_SECONDS = 60
DEFAULT_INSTRUMENT_CACHE_TTL_SECONDS = 86400


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
    provider: str = "upstox"


@dataclass
class InstrumentMeta:
    symbol: str
    instrument_key: str
    exchange: str
    trading_symbol: str
    preferred_ticker: str | None = None


_cache_lock = threading.Lock()
_quote_cache: dict[str, tuple[float, QuoteSnapshot]] = {}
_instrument_cache: dict[str, tuple[float, InstrumentMeta]] = {}


def _cache_ttl_seconds() -> int:
    settings = get_settings()
    ttl = getattr(settings, "market_data_cache_ttl_seconds", DEFAULT_CACHE_TTL_SECONDS)
    return max(10, ttl)


def _instrument_cache_ttl_seconds() -> int:
    return DEFAULT_INSTRUMENT_CACHE_TTL_SECONDS


def _cache_key(symbol: str) -> str:
    return symbol.strip().upper()


def _preferred_exchanges(symbol: str, preferred_ticker: str | None = None) -> list[str]:
    normalized = symbol.strip().upper()
    if normalized == "^NSEI":
        return ["NSE_INDEX", "NSE_EQ", "BSE_EQ"]

    preferred = (preferred_ticker or "").strip().upper()
    if preferred.endswith(".NS"):
        return ["NSE_EQ", "BSE_EQ"]
    if preferred.endswith(".BO") or preferred.endswith(".BSE"):
        return ["BSE_EQ", "NSE_EQ"]
    return ["NSE_EQ", "BSE_EQ"]


def _settings_token() -> str:
    settings = get_settings()
    token = getattr(settings, "upstox_access_token", "")
    if not token:
        raise MarketDataError("UPSTOX_ACCESS_TOKEN is not configured")
    return token


def _base_url() -> str:
    settings = get_settings()
    return getattr(settings, "upstox_base_url", "https://api.upstox.com/v2").rstrip("/")


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {_settings_token()}",
    }


def _from_quote_cache(symbol: str) -> QuoteSnapshot | None:
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


def _store_quote_cache(symbol: str, quote: QuoteSnapshot) -> QuoteSnapshot:
    with _cache_lock:
        _quote_cache[_cache_key(symbol)] = (time.time(), quote)
    return quote


def _from_instrument_cache(symbol: str) -> InstrumentMeta | None:
    key = _cache_key(symbol)
    with _cache_lock:
        cached = _instrument_cache.get(key)
        if not cached:
            return None
        cached_at, meta = cached
        if time.time() - cached_at > _instrument_cache_ttl_seconds():
            _instrument_cache.pop(key, None)
            return None
        return meta


def _store_instrument_cache(symbol: str, meta: InstrumentMeta) -> InstrumentMeta:
    with _cache_lock:
        _instrument_cache[_cache_key(symbol)] = (time.time(), meta)
    return meta


def _extract_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            return data["results"]
        return [value for value in data.values() if isinstance(value, dict)]
    return []


def _normalize_instrument(row: dict[str, Any], fallback_symbol: str, preferred_ticker: str | None = None) -> InstrumentMeta | None:
    instrument_key = (
        row.get("instrument_key")
        or row.get("instrument_token")
        or row.get("instrumentKey")
    )
    if not instrument_key:
        return None

    trading_symbol = (
        row.get("trading_symbol")
        or row.get("symbol")
        or row.get("tradingsymbol")
        or fallback_symbol
    )
    exchange = (
        row.get("exchange")
        or row.get("segment")
        or instrument_key.split("|", 1)[0]
    )
    return InstrumentMeta(
        symbol=fallback_symbol,
        instrument_key=str(instrument_key),
        exchange=str(exchange),
        trading_symbol=str(trading_symbol),
        preferred_ticker=preferred_ticker,
    )


def search_instrument(symbol: str, preferred_ticker: str | None = None) -> InstrumentMeta:
    cached = _from_instrument_cache(symbol)
    if cached:
        return cached

    normalized = symbol.strip().upper()
    query_value = "NIFTY 50" if normalized == "^NSEI" else normalized
    with httpx.Client(timeout=15.0) as client:
        for exchange in _preferred_exchanges(symbol, preferred_ticker):
            response = client.get(
                f"{_base_url()}/instruments/search",
                params={
                    "query": query_value,
                    "exchange": exchange,
                },
                headers=_headers(),
            )
            response.raise_for_status()
            payload = response.json()
            rows = _extract_candidates(payload)
            for row in rows:
                candidate = _normalize_instrument(row, normalized, preferred_ticker)
                if not candidate:
                    continue

                candidate_symbol = candidate.trading_symbol.upper()
                if normalized == "^NSEI" or candidate_symbol == normalized or candidate_symbol.startswith(normalized):
                    return _store_instrument_cache(symbol, candidate)

            if rows:
                candidate = _normalize_instrument(rows[0], normalized, preferred_ticker)
                if candidate:
                    return _store_instrument_cache(symbol, candidate)

    raise MarketDataError(f"Upstox instrument not found for {symbol}")


def _quote_from_upstox_entry(entry: dict[str, Any], meta: InstrumentMeta) -> QuoteSnapshot:
    ohlc = entry.get("ohlc") or {}
    price = float(entry.get("last_price") or 0)
    previous_close = float(ohlc.get("close") or 0)
    change = float(entry.get("net_change") or (price - previous_close))
    change_pct = (change / previous_close * 100) if previous_close else 0.0
    timestamp = str(entry.get("timestamp") or "")
    latest_trading_day = timestamp[:10] if len(timestamp) >= 10 else str(date.today())
    return QuoteSnapshot(
        provider_symbol=meta.trading_symbol,
        price=price,
        previous_close=previous_close,
        change=change,
        change_pct=change_pct,
        open=float(ohlc.get("open") or 0),
        high=float(ohlc.get("high") or 0),
        low=float(ohlc.get("low") or 0),
        volume=int(entry.get("volume") or 0),
        latest_trading_day=latest_trading_day,
        provider="upstox",
    )


def fetch_live_quotes_batch(requests_map: dict[str, str | None]) -> dict[str, QuoteSnapshot]:
    result: dict[str, QuoteSnapshot] = {}
    metas: dict[str, InstrumentMeta] = {}
    instrument_keys: list[str] = []

    for symbol, preferred_ticker in requests_map.items():
        cached = _from_quote_cache(symbol)
        if cached:
            result[symbol] = cached
            continue
        meta = search_instrument(symbol, preferred_ticker)
        metas[symbol] = meta
        instrument_keys.append(meta.instrument_key)

    if not instrument_keys:
        return result

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            f"{_base_url()}/market-quote/quotes",
            params={"instrument_key": ",".join(instrument_keys)},
            headers=_headers(),
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or {}

    keyed_by_instrument = {
        meta.instrument_key: symbol
        for symbol, meta in metas.items()
    }
    for instrument_key, entry in data.items():
        symbol = keyed_by_instrument.get(instrument_key)
        if not symbol:
            continue
        quote = _quote_from_upstox_entry(entry, metas[symbol])
        result[symbol] = _store_quote_cache(symbol, quote)

    return result


def fetch_live_quote(symbol: str, preferred_ticker: str | None = None) -> QuoteSnapshot:
    cached = _from_quote_cache(symbol)
    if cached:
        return cached

    quotes = fetch_live_quotes_batch({symbol: preferred_ticker})
    if symbol in quotes:
        return quotes[symbol]
    raise MarketDataError(f"Upstox quote not found for {symbol}")


def fetch_historical_daily(symbol: str, preferred_ticker: str | None = None, days: int = 365) -> list[dict[str, Any]]:
    meta = search_instrument(symbol, preferred_ticker)
    to_date = date.today()
    from_date = to_date - timedelta(days=days)
    encoded_key = quote(meta.instrument_key, safe="")

    with httpx.Client(timeout=20.0) as client:
        response = client.get(
            f"{_base_url()}/historical-candle/{encoded_key}/day/{to_date.isoformat()}/{from_date.isoformat()}",
            headers=_headers(),
        )
        response.raise_for_status()
        payload = response.json()

    candles = payload.get("data", {}).get("candles")
    if candles is None:
        candles = payload.get("data", [])
    if not isinstance(candles, list):
        return []

    rows: list[dict[str, Any]] = []
    for candle in candles:
        if not isinstance(candle, list) or len(candle) < 6:
            continue
        candle_date = str(candle[0])[:10]
        rows.append(
            {
                "date": candle_date,
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": int(candle[5]),
            }
        )
    return sorted(rows, key=lambda item: item["date"])


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


def get_quote_with_fallback(supabase: Client, symbol: str, preferred_ticker: str | None = None) -> QuoteSnapshot:
    try:
        return fetch_live_quote(symbol, preferred_ticker)
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
