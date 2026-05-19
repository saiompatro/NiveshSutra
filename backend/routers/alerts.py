from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID
from backend.models.db_models import Alert

router = APIRouter()


@router.get("/alerts")
async def list_alerts(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    alerts = (
        db.query(Alert)
        .filter(Alert.user_id == user_id)
        .order_by(Alert.created_at.desc())
        .limit(50)
        .all()
    )
    return [row_to_dict(a) for a in alerts]


@router.put("/alerts/{alert_id}/read")
async def mark_read(alert_id: str, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()
    if not alert:
        return None
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return row_to_dict(alert)


@router.put("/alerts/read-all")
async def mark_all_read(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    db.query(Alert).filter(Alert.user_id == user_id, Alert.is_read == False).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
