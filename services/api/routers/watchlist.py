from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client

router = APIRouter()


@router.get("/watchlist")
async def get_watchlist(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_client)):
    result = (
        supabase.table("watchlist")
        .select("*, stocks(*)")
        .eq("user_id", user["id"])
        .order("added_at", desc=True)
        .execute()
    )
    return result.data


@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("watchlist")
        .upsert({"user_id": user["id"], "symbol": symbol}, on_conflict="user_id,symbol")
        .execute()
    )
    return result.data[0] if result.data else None


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(
    symbol: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    supabase.table("watchlist").delete().eq("user_id", user["id"]).eq("symbol", symbol).execute()
    return {"status": "removed"}
