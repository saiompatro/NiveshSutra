from fastapi import APIRouter, Depends, Query
from supabase import Client

from ..dependencies import get_supabase_client
from ..services.market_data import get_quote_with_fallback, merge_live_quote_into_history

router = APIRouter()


@router.get("/stocks")
async def list_stocks(
    sector: str | None = None,
    supabase: Client = Depends(get_supabase_client),
):
    query = supabase.table("stocks").select("*").eq("active", True)
    if sector:
        query = query.eq("sector", sector)
    result = query.order("symbol").execute()
    return result.data


@router.get("/stocks/live")
async def list_stocks_live(
    sector: str | None = None,
    nifty50_only: bool = False,
    supabase: Client = Depends(get_supabase_client),
):
    query = supabase.table("stocks").select("symbol, company_name, sector, is_nifty50").eq("active", True)
    if sector:
        query = query.eq("sector", sector)
    if nifty50_only:
        query = query.eq("is_nifty50", True)
    stocks = query.order("symbol").execute().data or []

    signals = (
        supabase.table("signals")
        .select("symbol, signal, date")
        .order("date", desc=True)
        .limit(max(50, len(stocks) * 2))
        .execute()
        .data
        or []
    )
    signal_map: dict[str, str] = {}
    for row in signals:
        signal_map.setdefault(row["symbol"], row["signal"])

    enriched = []
    for stock in stocks:
        quote = get_quote_with_fallback(supabase, stock["symbol"])
        enriched.append(
            {
                "symbol": stock["symbol"],
                "company_name": stock.get("company_name") or "",
                "sector": stock.get("sector") or "",
                "current_price": quote.price,
                "change_pct": quote.change_pct,
                "signal": signal_map.get(stock["symbol"]),
                "provider": quote.provider,
            }
        )
    return enriched


@router.get("/stocks/{symbol}")
async def get_stock(symbol: str, supabase: Client = Depends(get_supabase_client)):
    result = supabase.table("stocks").select("*").eq("symbol", symbol).single().execute()
    return result.data


@router.get("/stocks/{symbol}/quote")
async def get_stock_quote(symbol: str, supabase: Client = Depends(get_supabase_client)):
    stock = supabase.table("stocks").select("symbol, company_name, sector").eq("symbol", symbol).single().execute().data
    if not stock:
        return None

    quote = get_quote_with_fallback(supabase, symbol)
    return {
        "symbol": stock["symbol"],
        "company_name": stock.get("company_name") or "",
        "sector": stock.get("sector") or "",
        "current_price": quote.price,
        "change_pct": quote.change_pct,
        "change": quote.change,
        "day_high": quote.high,
        "day_low": quote.low,
        "volume": quote.volume,
        "market_cap": 0,
        "provider": quote.provider,
        "latest_trading_day": quote.latest_trading_day,
    }


@router.get("/stocks/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    days: int = Query(default=90, le=3650),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("ohlcv")
        .select("*")
        .eq("symbol", symbol)
        .order("date", desc=True)
        .limit(days)
        .execute()
    )
    rows = sorted(result.data or [], key=lambda x: x["date"])
    try:
        quote = get_quote_with_fallback(supabase, symbol)
        rows = merge_live_quote_into_history(rows, quote)
    except Exception:
        pass
    return rows


@router.get("/stocks/{symbol}/indicators")
async def get_indicators(
    symbol: str,
    days: int = Query(default=30, le=365),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("technical_indicators")
        .select("*")
        .eq("symbol", symbol)
        .order("date", desc=True)
        .limit(days)
        .execute()
    )
    return sorted(result.data, key=lambda x: x["date"])
