from pydantic import BaseModel
from typing import Optional


class HoldingCreate(BaseModel):
    symbol: str
    quantity: float
    avg_buy_price: float
    buy_date: str
    notes: Optional[str] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_buy_price: Optional[float] = None
    notes: Optional[str] = None
