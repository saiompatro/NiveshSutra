from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client

router = APIRouter()


@router.get("/alerts")
async def list_alerts(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_client)):
    result = (
        supabase.table("alerts")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data


@router.put("/alerts/{alert_id}/read")
async def mark_read(
    alert_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("alerts")
        .update({"is_read": True})
        .eq("id", alert_id)
        .eq("user_id", user["id"])
        .execute()
    )
    return result.data[0] if result.data else None


@router.put("/alerts/read-all")
async def mark_all_read(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_client)):
    supabase.table("alerts").update({"is_read": True}).eq("user_id", user["id"]).eq("is_read", False).execute()
    return {"status": "ok"}
