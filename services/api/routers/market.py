from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_supabase_client

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
