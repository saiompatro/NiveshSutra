from pydantic import BaseModel
from typing import Optional


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    risk_profile: Optional[str] = None
    risk_score: Optional[int] = None


class RiskAssessmentRequest(BaseModel):
    answers: list[int]  # 5 answers, each 1-3
