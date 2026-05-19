from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID
from backend.models.db_models import Profile
from ..models.profile import RiskAssessmentRequest, ProfileUpdate

router = APIRouter()


@router.get("/profile")
async def get_profile(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return row_to_dict(profile)


@router.put("/profile")
async def update_profile(body: ProfileUpdate, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        return None
    data = body.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return row_to_dict(profile)


@router.post("/profile/risk-assessment")
async def submit_risk_assessment(body: RiskAssessmentRequest, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    total = sum(body.answers)
    if total <= 8:
        risk_profile = "conservative"
    elif total <= 12:
        risk_profile = "moderate"
    else:
        risk_profile = "aggressive"

    profile = db.query(Profile).filter(Profile.id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.risk_score = total
    profile.risk_profile = risk_profile
    profile.onboarding_complete = True
    db.commit()
    db.refresh(profile)
    return {"risk_score": total, "risk_profile": risk_profile, "profile": row_to_dict(profile)}
