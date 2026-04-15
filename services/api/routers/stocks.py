from fastapi import APIRouter, Depends, Query
from supabase import Client
from ..dependencies import get_supabase_client

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


@router.get("/stocks/{symbol}")
async def get_stock(symbol: str, supabase: Client = Depends(get_supabase_client)):
    result = supabase.table("stocks").select("*").eq("symbol", symbol).single().execute()
    return result.data


@router.get("/stocks/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    days: int = Query(default=90, le=365),
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
    return sorted(result.data, key=lambda x: x["date"])


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
