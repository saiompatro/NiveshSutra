from pydantic import BaseModel, Field
from typing import Literal, Optional


class OptimizeRequest(BaseModel):
    portfolio_value: Optional[float] = Field(default=None, gt=0, le=1_000_000_000)
    method_override: Optional[Literal["conservative", "moderate", "aggressive"]] = None
    target_return: Optional[float] = Field(default=None, ge=-1.0, le=5.0)
    target_risk: Optional[float] = Field(default=None, ge=0.0, le=5.0)


class MonteCarloRiskRequest(BaseModel):
    scenarios: int = Field(default=10_000, ge=1_000, le=50_000)
    horizon_days: int = Field(default=1, ge=1, le=30)
    lookback_days: int = Field(default=756, ge=60, le=1_260)
    confidence_levels: list[float] = Field(default_factory=lambda: [0.95, 0.99], min_length=1, max_length=5)
    risk_free_rate: Optional[float] = Field(default=None, ge=-0.05, le=0.25)
    seed: Optional[int] = None
    sampling_method: Literal["auto", "sobol", "halton", "pseudo_random", "antithetic"] = "auto"
    importance_sampling: bool = True
    importance_shift: float = Field(default=1.25, ge=0.0, le=5.0)
