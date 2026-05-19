from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID
from backend.models.db_models import Stock, Ohlcv
from ..services.market_data import fetch_historical_daily, fetch_live_quote, search_instrument
from ..validation import require_stock_symbol

router = APIRouter()


@router.get("/stocks/search")
async def search_stock(
    q: str,
    db: Session = Depends(get_db),
):
    """
    Search for a stock by symbol. If it exists in the DB, return it.
    If not, validate via the free market data provider and add it to the stocks table.
    """
    symbol = require_stock_symbol(q)

    # Check if stock already exists
    existing = db.query(Stock).filter(Stock.symbol == symbol).first()
    if existing:
        return {"stock": row_to_dict(existing), "source": "database"}

    # Try to validate with the free provider stack.
    try:
        instrument = search_instrument(symbol)
        fetch_live_quote(symbol)

        # We only persist the minimal stock metadata required by the app.
        name = instrument.company_name or symbol
        sector = "Unknown"
        industry = "Unknown"
        cap_category = "unknown"

        stock = Stock(
            symbol=symbol,
            yf_ticker=instrument.instrument_key,
            company_name=name,
            sector=sector,
            industry=industry,
            market_cap_category=cap_category,
            is_nifty50=False,
            active=True,
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

        # Fetch initial OHLCV data (last 90 days) in background
        try:
            _fetch_initial_ohlcv(db, symbol)
        except Exception:
            pass  # Non-critical; data will be fetched by next pipeline run

        return {"stock": row_to_dict(stock), "source": "yfinance"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find stock '{symbol}': {str(e)}",
        )


def _fetch_initial_ohlcv(db: Session, symbol: str) -> None:
    """Fetch last 90 days of OHLCV data for a newly added stock."""
    try:
        rows = fetch_historical_daily(symbol, days=90)
        if not rows:
            return
        for row in rows:
            existing = (
                db.query(Ohlcv)
                .filter(Ohlcv.symbol == symbol, Ohlcv.date == row["date"])
                .first()
            )
            if existing:
                existing.open = round(float(row["open"]), 2)
                existing.high = round(float(row["high"]), 2)
                existing.low = round(float(row["low"]), 2)
                existing.close = round(float(row["close"]), 2)
                existing.volume = int(row["volume"])
            else:
                db.add(Ohlcv(
                    symbol=symbol,
                    date=row["date"],
                    open=round(float(row["open"]), 2),
                    high=round(float(row["high"]), 2),
                    low=round(float(row["low"]), 2),
                    close=round(float(row["close"]), 2),
                    volume=int(row["volume"]),
                ))
        db.commit()
    except Exception as e:
        print(f"Initial OHLCV fetch failed for {symbol}: {e}")
