from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from ..dependencies import get_supabase_admin, get_current_user

router = APIRouter()


@router.get("/stocks/search")
async def search_stock(
    q: str = Query(..., min_length=1, max_length=20, description="Stock symbol to search"),
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
):
    """
    Search for a stock by symbol. If it exists in the DB, return it.
    If not, validate via Alpha Vantage and add it to the stocks table.
    """
    symbol = q.strip().upper().replace(".NS", "")

    # Check if stock already exists
    result = supabase.table("stocks").select("*").eq("symbol", symbol).execute()
    if result.data:
        return {"stock": result.data[0], "source": "database"}

    # Try to fetch from Alpha Vantage
    try:
        from services.ml.ingest.alpha_vantage_utils import fetch_alpha_vantage_daily
        import requests

        av_symbol = f"{symbol}.NS"
        # Fetch daily data to validate symbol and get company name
        df = fetch_alpha_vantage_daily(av_symbol, outputsize="compact")
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Stock '{symbol}' not found on NSE via Alpha Vantage. Please check the symbol.",
            )

        # Alpha Vantage does not provide company name/sector/industry in free tier, so use symbol as name
        name = symbol
        sector = "Unknown"
        industry = "Unknown"
        cap_category = "unknown"

        stock_data = {
            "symbol": symbol,
            "yf_ticker": av_symbol,
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

        return {"stock": insert_result.data[0], "source": "alpha_vantage"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find stock '{symbol}': {str(e)}",
        )


def _fetch_initial_ohlcv(supabase: Client, symbol: str) -> None:
    """Fetch last 90 days of OHLCV data for a newly added stock using Alpha Vantage."""
    from services.ml.ingest.alpha_vantage_utils import fetch_alpha_vantage_daily
    av_symbol = f"{symbol}.NS"
    try:
        df = fetch_alpha_vantage_daily(av_symbol, outputsize="compact")
        if df.empty:
            return
        # Only keep last 90 days
        df = df.sort_values("date").tail(90)
        rows = []
        for _, r in df.iterrows():
            date_str = r["date"].strftime("%Y-%m-%d")
            rows.append({
                "symbol": symbol,
                "date": date_str,
                "open": round(float(r["open"]), 2),
                "high": round(float(r["high"]), 2),
                "low": round(float(r["low"]), 2),
                "close": round(float(r["close"]), 2),
                "volume": int(r["volume"]),
            })
        if rows:
            supabase.table("ohlcv").upsert(rows, on_conflict="symbol,date").execute()
    except Exception as e:
        print(f"Alpha Vantage OHLCV fetch failed for {symbol}: {e}")
