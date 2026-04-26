from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, timedelta
import re
import threading
import time
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup
from supabase import Client
import yfinance as yf

from ..config import get_settings


DEFAULT_CACHE_TTL_SECONDS = 60
DEFAULT_INSTRUMENT_CACHE_TTL_SECONDS = 86400
MONEYCONTROL_MARKETS_URL = "https://www.moneycontrol.com/stocksmarketsindia/"
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


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
    provider: str = "yfinance"


@dataclass
class InstrumentMeta:
    symbol: str
    instrument_key: str
    exchange: str
    trading_symbol: str
    preferred_ticker: str | None = None
    company_name: str | None = None


_cache_lock = threading.Lock()
_quote_cache: dict[str, tuple[float, QuoteSnapshot]] = {}
_instrument_cache: dict[str, tuple[float, InstrumentMeta]] = {}


def _cache_ttl_seconds() -> int:
    settings = get_settings()
    ttl = getattr(settings, "market_data_cache_ttl_seconds", DEFAULT_CACHE_TTL_SECONDS)
    return max(10, ttl)


def _instrument_cache_ttl_seconds() -> int:
    return DEFAULT_INSTRUMENT_CACHE_TTL_SECONDS


def _cache_key(symbol: str, preferred_ticker: str | None = None) -> str:
    normalized_symbol = symbol.strip().upper()
    normalized_ticker = (preferred_ticker or "").strip().upper()
    return f"{normalized_symbol}::{normalized_ticker}"


def _request_headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }


def _from_quote_cache(symbol: str, preferred_ticker: str | None = None) -> QuoteSnapshot | None:
    key = _cache_key(symbol, preferred_ticker)
    with _cache_lock:
        cached = _quote_cache.get(key)
        if not cached:
            return None
        cached_at, quote = cached
        if time.time() - cached_at > _cache_ttl_seconds():
            _quote_cache.pop(key, None)
            return None
        return quote


def _store_quote_cache(
    symbol: str,
    quote: QuoteSnapshot,
    preferred_ticker: str | None = None,
) -> QuoteSnapshot:
    with _cache_lock:
        _quote_cache[_cache_key(symbol, preferred_ticker)] = (time.time(), quote)
    return quote


def _from_instrument_cache(symbol: str, preferred_ticker: str | None = None) -> InstrumentMeta | None:
    key = _cache_key(symbol, preferred_ticker)
    with _cache_lock:
        cached = _instrument_cache.get(key)
        if not cached:
            return None
        cached_at, meta = cached
        if time.time() - cached_at > _instrument_cache_ttl_seconds():
            _instrument_cache.pop(key, None)
            return None
        return meta


def _store_instrument_cache(
    symbol: str,
    meta: InstrumentMeta,
    preferred_ticker: str | None = None,
) -> InstrumentMeta:
    with _cache_lock:
        _instrument_cache[_cache_key(symbol, preferred_ticker)] = (time.time(), meta)
    return meta


def _normalize_symbol_query(symbol: str) -> str:
    normalized = symbol.strip().upper()
    for suffix in (".NS", ".NSE", ".BSE", ".BO"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


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


def _candidate_tickers(symbol: str, preferred_ticker: str | None = None) -> list[str]:
    normalized = symbol.strip().upper()
    preferred = (preferred_ticker or "").strip().upper()
    preferred = preferred.replace(".NSE", ".NS").replace(".BSE", ".BO")

    if preferred:
        return [preferred]
    if normalized in {"^NSEI", "^BSESN"}:
        return [normalized]
    if normalized.endswith((".NS", ".BO")):
        return [normalized]
    return [f"{normalized}.NS", f"{normalized}.BO"]


def _safe_history(provider_symbol: str, days: int = 30) -> pd.DataFrame:
    start = date.today() - timedelta(days=max(days + 10, 20))
    end = date.today() + timedelta(days=1)

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            history = yf.Ticker(provider_symbol).history(
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1d",
                actions=False,
            )
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    else:
        raise MarketDataError(f"yfinance failed for {provider_symbol} after 3 attempts") from last_exc

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


def _safe_info(provider_symbol: str) -> dict[str, Any]:
    try:
        return dict(yf.Ticker(provider_symbol).info or {})
    except Exception:
        return {}


def _quote_from_yfinance(meta: InstrumentMeta) -> QuoteSnapshot:
    history = _safe_history(meta.instrument_key, days=10)
    fast_info = _safe_fast_info(meta.instrument_key)

    if history.empty and not fast_info:
        raise MarketDataError(f"Quote not available for {meta.instrument_key}")

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
    latest_trading_day = str(latest.get("date") or date.today().isoformat())

    return QuoteSnapshot(
        provider_symbol=meta.instrument_key,
        price=price,
        previous_close=previous_close,
        change=change,
        change_pct=change_pct,
        open=_coerce_float(fast_info.get("open"), _coerce_float(latest.get("open"), price)),
        high=_coerce_float(
            fast_info.get("dayHigh"),
            _coerce_float(fast_info.get("regularMarketDayHigh"), _coerce_float(latest.get("high"), price)),
        ),
        low=_coerce_float(
            fast_info.get("dayLow"),
            _coerce_float(fast_info.get("regularMarketDayLow"), _coerce_float(latest.get("low"), price)),
        ),
        volume=_coerce_int(
            fast_info.get("lastVolume"),
            _coerce_int(fast_info.get("regularMarketVolume"), _coerce_int(latest.get("volume"))),
        ),
        latest_trading_day=latest_trading_day,
        provider="yfinance",
    )


def _parse_moneycontrol_snapshot(label: str, html: str) -> QuoteSnapshot | None:
    patterns = [
        re.compile(
            rf"{re.escape(label)}\s*([0-9,]+\.\d+)\s*([+-]?[0-9,]+\.\d+)\s*([+-]?[0-9,]+\.\d+)%",
            re.IGNORECASE,
        ),
        re.compile(
            rf"{re.escape(label)}.*?([0-9,]+\.\d+).*?([+-]?[0-9,]+\.\d+).*?([+-]?[0-9,]+\.\d+)%",
            re.IGNORECASE | re.DOTALL,
        ),
    ]
    for pattern in patterns:
        match = pattern.search(html)
        if not match:
            continue
        price = _coerce_float(match.group(1).replace(",", ""))
        change = _coerce_float(match.group(2).replace(",", ""))
        change_pct = _coerce_float(match.group(3).replace(",", ""))
        previous_close = price - change
        return QuoteSnapshot(
            provider_symbol=label,
            price=price,
            previous_close=previous_close,
            change=change,
            change_pct=change_pct,
            open=price,
            high=price,
            low=price,
            volume=0,
            latest_trading_day=date.today().isoformat(),
            provider="moneycontrol",
        )
    return None


def _fetch_moneycontrol_index_snapshot(symbol: str) -> QuoteSnapshot | None:
    label_map = {
        "^NSEI": "NIFTY 50",
        "^BSESN": "SENSEX",
    }
    label = label_map.get(symbol.strip().upper())
    if not label:
        return None

    try:
        response = requests.get(
            MONEYCONTROL_MARKETS_URL,
            headers=_request_headers(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    html = response.text
    snapshot = _parse_moneycontrol_snapshot(label, html)
    if snapshot:
        return snapshot

    # Fall back to a text-only parse in case the markup changes but values still
    # appear in the rendered document.
    text = " ".join(BeautifulSoup(html, "html.parser").stripped_strings)
    return _parse_moneycontrol_snapshot(label, text)


def search_instrument(symbol: str, preferred_ticker: str | None = None) -> InstrumentMeta:
    cached = _from_instrument_cache(symbol, preferred_ticker)
    if cached:
        return cached

    normalized = _normalize_symbol_query(symbol)
    if normalized in {"^NSEI", "^BSESN"}:
        meta = InstrumentMeta(
            symbol=normalized,
            instrument_key=normalized,
            exchange="INDEX",
            trading_symbol="NIFTY 50" if normalized == "^NSEI" else "SENSEX",
            preferred_ticker=normalized,
            company_name="NIFTY 50" if normalized == "^NSEI" else "SENSEX",
        )
        return _store_instrument_cache(symbol, meta, preferred_ticker)

    last_error: Exception | None = None
    for candidate in _candidate_tickers(normalized, preferred_ticker):
        try:
            history = _safe_history(candidate, days=10)
            fast_info = _safe_fast_info(candidate)
            if history.empty and not fast_info:
                continue

            info = _safe_info(candidate)
            meta = InstrumentMeta(
                symbol=normalized,
                instrument_key=candidate,
                exchange="NSE" if candidate.endswith(".NS") else "BSE",
                trading_symbol=normalized,
                preferred_ticker=candidate,
                company_name=(
                    info.get("shortName")
                    or info.get("longName")
                    or info.get("displayName")
                    or normalized
                ),
            )
            return _store_instrument_cache(symbol, meta, preferred_ticker)
        except Exception as exc:
            last_error = exc

    if last_error:
        raise MarketDataError(str(last_error)) from last_error
    raise MarketDataError(f"Instrument not found for {symbol}")


def _fetch_quote(symbol: str, preferred_ticker: str | None = None) -> QuoteSnapshot:
    normalized = _normalize_symbol_query(symbol)
    if normalized in {"^NSEI", "^BSESN"}:
        moneycontrol_snapshot = _fetch_moneycontrol_index_snapshot(normalized)
        if moneycontrol_snapshot:
            return moneycontrol_snapshot

    meta = search_instrument(symbol, preferred_ticker)
    return _quote_from_yfinance(meta)


def fetch_live_quotes_batch(requests_map: dict[str, str | None]) -> dict[str, QuoteSnapshot]:
    result: dict[str, QuoteSnapshot] = {}
    pending: list[tuple[str, str | None]] = []

    for symbol, preferred_ticker in requests_map.items():
        cached = _from_quote_cache(symbol, preferred_ticker)
        if cached:
            result[symbol] = cached
        else:
            pending.append((symbol, preferred_ticker))

    if not pending:
        return result

    max_workers = min(8, len(pending))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_fetch_quote, symbol, preferred_ticker): (symbol, preferred_ticker)
            for symbol, preferred_ticker in pending
        }
        for future in as_completed(future_map):
            symbol, preferred_ticker = future_map[future]
            try:
                quote = future.result()
            except Exception:
                continue
            result[symbol] = _store_quote_cache(symbol, quote, preferred_ticker)

    return result


def fetch_live_quote(symbol: str, preferred_ticker: str | None = None) -> QuoteSnapshot:
    cached = _from_quote_cache(symbol, preferred_ticker)
    if cached:
        return cached

    quote = _fetch_quote(symbol, preferred_ticker)
    return _store_quote_cache(symbol, quote, preferred_ticker)


def fetch_historical_daily(symbol: str, preferred_ticker: str | None = None, days: int = 365) -> list[dict[str, Any]]:
    meta = search_instrument(symbol, preferred_ticker)
    history = _safe_history(meta.instrument_key, days=days)
    if history.empty:
        return []

    rows: list[dict[str, Any]] = []
    for _, candle in history.tail(days).iterrows():
        rows.append(
            {
                "date": str(candle["date"]),
                "open": _coerce_float(candle["open"]),
                "high": _coerce_float(candle["high"]),
                "low": _coerce_float(candle["low"]),
                "close": _coerce_float(candle["close"]),
                "volume": _coerce_int(candle["volume"]),
            }
        )
    return rows


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
