from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID
from backend.models.db_models import SignalNotification

router = APIRouter()


class NotificationPreference(BaseModel):
    email_notifications_enabled: bool


@router.get("/notifications/tracked")
async def get_tracked_signals(db: Session = Depends(get_db)):
    """Get all actively tracked signal notifications for the current user."""
    user_id = DEFAULT_USER_ID
    rows = (
        db.query(SignalNotification)
        .filter(
            SignalNotification.user_id == user_id,
            SignalNotification.is_active == True,
        )
        .order_by(SignalNotification.created_at.desc())
        .all()
    )
    return [row_to_dict(r) for r in rows]


@router.delete("/notifications/tracked/{notification_id}")
async def stop_tracking_signal(notification_id: str, db: Session = Depends(get_db)):
    """Stop tracking a signal notification."""
    user_id = DEFAULT_USER_ID
    notif = (
        db.query(SignalNotification)
        .filter(
            SignalNotification.id == notification_id,
            SignalNotification.user_id == user_id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_active = False
    db.commit()
    return {"status": "stopped"}
