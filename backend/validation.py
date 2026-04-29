from __future__ import annotations

import re

from fastapi import HTTPException, status

STOCK_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9&.\-]{1,20}$")
MAX_QUOTE_SYMBOLS = 25


def normalize_stock_symbol(value: str) -> str:
    return (
        value.strip()
        .upper()
        .replace(".NS", "")
        .replace(".BSE", "")
        .replace(".NSE", "")
    )


def require_stock_symbol(value: str) -> str:
    symbol = normalize_stock_symbol(value)
    if not STOCK_SYMBOL_PATTERN.fullmatch(symbol):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Stock symbol must be 1-20 chars: A-Z, 0-9, ampersand, dot, or hyphen",
        )
    return symbol
