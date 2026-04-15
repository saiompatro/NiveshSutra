from fastapi import APIRouter, Depends
from supabase import Client
from ..dependencies import get_current_user, get_supabase_client
from ..models.profile import RiskAssessmentRequest, ProfileUpdate

router = APIRouter()


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase_client)):
    result = supabase.table("profiles").select("*").eq("id", user["id"]).single().execute()
    return result.data


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    data = body.model_dump(exclude_none=True)
    result = supabase.table("profiles").update(data).eq("id", user["id"]).execute()
    return result.data[0] if result.data else None


@router.post("/profile/risk-assessment")
async def submit_risk_assessment(
    body: RiskAssessmentRequest,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
):
    total = sum(body.answers)
    if total <= 8:
        risk_profile = "conservative"
    elif total <= 12:
        risk_profile = "moderate"
    else:
        risk_profile = "aggressive"

    result = (
        supabase.table("profiles")
        .update({"risk_score": total, "risk_profile": risk_profile, "onboarding_complete": True})
        .eq("id", user["id"])
        .execute()
    )
    return {"risk_score": total, "risk_profile": risk_profile, "profile": result.data[0] if result.data else None}
