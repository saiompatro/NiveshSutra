from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_supabase_client
from ..services.market_data import get_quote_with_fallback

router = APIRouter()


@router.get("/market/overview")
async def market_overview(supabase: Client = Depends(get_supabase_client)):
    # Get latest OHLCV for all stocks to compute gainers/losers
    result = supabase.rpc("get_market_overview").execute()
    if result.data:
        return result.data

    # Fallback: get latest prices manually
    stocks = supabase.table("stocks").select("symbol, company_name, sector").eq("active", True).execute()
    overview = []
    for stock in stocks.data or []:
        ohlcv = (
            supabase.table("ohlcv")
            .select("close, date")
            .eq("symbol", stock["symbol"])
            .order("date", desc=True)
            .limit(2)
            .execute()
        )
        if ohlcv.data and len(ohlcv.data) >= 2:
            current = float(ohlcv.data[0]["close"])
            previous = float(ohlcv.data[1]["close"])
            change_pct = ((current - previous) / previous) * 100
            overview.append({
                **stock,
                "price": current,
                "change_pct": round(change_pct, 2),
                "date": ohlcv.data[0]["date"],
            })
    overview.sort(key=lambda x: x.get("change_pct", 0), reverse=True)
    return overview


@router.get("/market/index-overview")
async def market_index_overview(supabase: Client = Depends(get_supabase_client)):
    try:
        quote = get_quote_with_fallback(supabase, "^NSEI")
        return {
            "nifty50_value": quote.price,
            "nifty50_change": quote.change,
            "nifty50_change_pct": quote.change_pct,
            "provider": quote.provider,
        }
    except Exception:
        data = (
            supabase.table("ohlcv")
            .select("close, date")
            .eq("symbol", "^NSEI")
            .order("date", desc=True)
            .limit(2)
            .execute()
            .data
            or []
        )
        if not data:
            return None

        latest = float(data[0]["close"])
        previous = float(data[1]["close"]) if len(data) > 1 else latest
        change = latest - previous
        change_pct = (change / previous * 100) if previous else 0
        return {
            "nifty50_value": latest,
            "nifty50_change": change,
            "nifty50_change_pct": change_pct,
            "provider": "supabase",
        }
