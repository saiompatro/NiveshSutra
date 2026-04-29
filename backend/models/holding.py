from pydantic import BaseModel, Field, field_validator
from typing import Optional


def _normalize_symbol(value: str) -> str:
    return (
        value.strip()
        .upper()
        .replace(".NS", "")
        .replace(".BSE", "")
        .replace(".NSE", "")
    )


class HoldingCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20, pattern=r"^[A-Z0-9&.\-]+$")
    quantity: float = Field(gt=0, le=1_000_000)
    avg_buy_price: float = Field(gt=0, le=10_000_000)
    buy_date: str = Field(min_length=8, max_length=10)
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _normalize_symbol(str(value))


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(default=None, gt=0, le=1_000_000)
    avg_buy_price: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    notes: Optional[str] = Field(default=None, max_length=500)
