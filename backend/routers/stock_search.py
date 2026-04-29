from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from ..dependencies import get_supabase_admin, get_current_user
from ..services.market_data import fetch_historical_daily, fetch_live_quote, search_instrument
from ..validation import require_stock_symbol

router = APIRouter()


@router.get("/stocks/search")
async def search_stock(
    q: str = Query(..., min_length=1, max_length=20, description="Stock symbol to search"),
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
):
    """
    Search for a stock by symbol. If it exists in the DB, return it.
    If not, validate via the free market data provider and add it to the stocks table.
    """
    symbol = require_stock_symbol(q)

    # Check if stock already exists
    result = supabase.table("stocks").select("*").eq("symbol", symbol).execute()
    if result.data:
        return {"stock": result.data[0], "source": "database"}

    # Try to validate with the free provider stack.
    try:
        instrument = search_instrument(symbol)
        fetch_live_quote(symbol)

        # We only persist the minimal stock metadata required by the app.
        name = instrument.company_name or symbol
        sector = "Unknown"
        industry = "Unknown"
        cap_category = "unknown"

        stock_data = {
            "symbol": symbol,
            "yf_ticker": instrument.instrument_key,
            "company_name": name,
            "sector": sector,
            "industry": industry,
            "market_cap_category": cap_category,
            "is_nifty50": False,
            "active": True,
        }

        insert_result = supabase.table("stocks").insert(stock_data).execute()
        if not insert_result.data:
            raise HTTPException(status_code=500, detail="Failed to add stock to database")

        # Fetch initial OHLCV data (last 90 days) in background
        try:
            _fetch_initial_ohlcv(supabase, symbol)
        except Exception:
            pass  # Non-critical; data will be fetched by next pipeline run

        return {"stock": insert_result.data[0], "source": "yfinance"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find stock '{symbol}': {str(e)}",
        )


def _fetch_initial_ohlcv(supabase: Client, symbol: str) -> None:
    """Fetch last 90 days of OHLCV data for a newly added stock."""
    try:
        rows = fetch_historical_daily(symbol, days=90)
        if not rows:
            return
        upsert_rows = [
            {
                "symbol": symbol,
                "date": row["date"],
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["close"]), 2),
                "volume": int(row["volume"]),
            }
            for row in rows
        ]
        if upsert_rows:
            supabase.table("ohlcv").upsert(upsert_rows, on_conflict="symbol,date").execute()
    except Exception as e:
        print(f"Initial OHLCV fetch failed for {symbol}: {e}")
