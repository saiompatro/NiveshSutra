from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client
from ..models.holding import HoldingCreate, HoldingUpdate
from ..services.market_data import fetch_live_quotes_batch, get_quote_with_fallback

router = APIRouter()


@router.get("/holdings")
async def list_holdings(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_client)):
    result = (
        supabase.table("holdings")
        .select("*, stocks(*)")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.get("/holdings/live")
async def list_holdings_live(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    holdings = (
        supabase.table("holdings")
        .select("id, symbol, quantity, avg_buy_price, buy_date, notes, stocks(yf_ticker)")
        .eq("user_id", user["id"])
        .execute()
        .data
        or []
    )

    quote_map = fetch_live_quotes_batch(
        {
            holding["symbol"]: (holding.get("stocks") or {}).get("yf_ticker")
            for holding in holdings
        }
    )

    enriched = []
    for holding in holdings:
        stock_info = holding.get("stocks") or {}
        quote = quote_map.get(holding["symbol"]) or get_quote_with_fallback(
            supabase, holding["symbol"], stock_info.get("yf_ticker")
        )
        avg_price = float(holding.get("avg_buy_price") or 0)
        quantity = float(holding.get("quantity") or 0)
        value = quote.price * quantity
        invested = avg_price * quantity
        pnl = value - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        enriched.append(
            {
                "id": holding["id"],
                "symbol": holding["symbol"],
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": quote.price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "value": value,
                "provider": quote.provider,
            }
        )
    return enriched


@router.post("/holdings")
async def create_holding(
    body: HoldingCreate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    data = body.model_dump()
    data["user_id"] = user["id"]
    result = supabase.table("holdings").insert(data).execute()
    return result.data[0] if result.data else None


@router.put("/holdings/{holding_id}")
async def update_holding(
    holding_id: str,
    body: HoldingUpdate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    data = body.model_dump(exclude_none=True)
    result = (
        supabase.table("holdings")
        .update(data)
        .eq("id", holding_id)
        .eq("user_id", user["id"])
        .execute()
    )
    return result.data[0] if result.data else None


@router.delete("/holdings/{holding_id}")
async def delete_holding(
    holding_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    supabase.table("holdings").delete().eq("id", holding_id).eq("user_id", user["id"]).execute()
    return {"status": "deleted"}
