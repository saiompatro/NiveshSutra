from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client
from ..dependencies import get_supabase_admin, get_current_user

router = APIRouter()


class NotificationPreference(BaseModel):
    email_notifications_enabled: bool


@router.get("/notifications/tracked")
async def get_tracked_signals(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
):
    """Get all actively tracked signal notifications for the current user."""
    result = (
        supabase.table("signal_notifications")
        .select("id, symbol, last_signal, last_notified_at, is_active, created_at")
        .eq("user_id", user["id"])
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.delete("/notifications/tracked/{notification_id}")
async def stop_tracking_signal(
    notification_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin),
):
    """Stop tracking a signal notification."""
    result = (
        supabase.table("signal_notifications")
        .update({"is_active": False})
        .eq("id", notification_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "stopped"}
