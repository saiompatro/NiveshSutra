from pydantic import BaseModel
from typing import Optional


class OptimizeRequest(BaseModel):
    portfolio_value: Optional[float] = None
    method_override: Optional[str] = None
    target_return: Optional[float] = None
    target_risk: Optional[float] = None
