from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=120)
    risk_profile: Optional[str] = Field(
        default=None,
        pattern=r"^(conservative|moderate|aggressive)$",
    )
    risk_score: Optional[int] = Field(default=None, ge=5, le=15)


class RiskAssessmentRequest(BaseModel):
    answers: list[int] = Field(min_length=5, max_length=5)  # 5 answers, each 1-3

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, value: list[int]) -> list[int]:
        if any(answer < 1 or answer > 3 for answer in value):
            raise ValueError("Each answer must be between 1 and 3")
        return value
