from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client
from ..models.holding import HoldingCreate, HoldingUpdate

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
