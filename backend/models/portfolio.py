from pydantic import BaseModel, Field
from typing import Optional


class OptimizeRequest(BaseModel):
    portfolio_value: Optional[float] = None
    method_override: Optional[str] = None
    target_return: Optional[float] = None
    target_risk: Optional[float] = None


class MonteCarloRiskRequest(BaseModel):
    scenarios: int = 10_000
    horizon_days: int = 1
    lookback_days: int = 756
    confidence_levels: list[float] = Field(default_factory=lambda: [0.95, 0.99])
    risk_free_rate: Optional[float] = None
    seed: Optional[int] = None
