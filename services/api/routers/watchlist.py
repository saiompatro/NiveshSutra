from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client
from ..services.market_data import get_quote_with_fallback

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


@router.get("/watchlist/live")
async def get_watchlist_live(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    rows = (
        supabase.table("watchlist")
        .select("symbol, stocks(company_name)")
        .eq("user_id", user["id"])
        .order("added_at", desc=True)
        .execute()
        .data
        or []
    )

    items = []
    for row in rows:
        quote = get_quote_with_fallback(supabase, row["symbol"])
        stock_info = row.get("stocks") or {}
        items.append(
            {
                "symbol": row["symbol"],
                "company_name": stock_info.get("company_name") or "",
                "current_price": quote.price,
                "change_pct": quote.change_pct,
                "provider": quote.provider,
            }
        )
    return items


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
