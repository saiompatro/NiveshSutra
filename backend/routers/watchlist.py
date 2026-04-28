from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_for_user
from ..services.market_data import fetch_live_quotes_batch, get_quote_with_fallback

router = APIRouter()


@router.get("/watchlist")
async def get_watchlist(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_for_user)):
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
    supabase: Client = Depends(get_supabase_for_user),
):
    rows = (
        supabase.table("watchlist")
        .select("symbol, stocks(company_name, yf_ticker)")
        .eq("user_id", user["id"])
        .order("added_at", desc=True)
        .execute()
        .data
        or []
    )

    quote_map = fetch_live_quotes_batch(
        {
            row["symbol"]: (row.get("stocks") or {}).get("yf_ticker")
            for row in rows
        }
    )

    items = []
    for row in rows:
        stock_info = row.get("stocks") or {}
        quote = quote_map.get(row["symbol"]) or get_quote_with_fallback(
            supabase, row["symbol"], stock_info.get("yf_ticker")
        )
        items.append(
            {
                "symbol": row["symbol"],
                "company_name": stock_info.get("company_name") or "",
                "current_price": quote.price,
                "previous_close": quote.previous_close,
                "change": quote.change,
                "change_pct": quote.change_pct,
                "provider": quote.provider,
            }
        )
    return items


@router.post("/watchlist/{symbol}")
async def add_to_watchlist(
    symbol: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_for_user),
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
    supabase: Client = Depends(get_supabase_for_user),
):
    supabase.table("watchlist").delete().eq("user_id", user["id"]).eq("symbol", symbol).execute()
    return {"status": "removed"}
