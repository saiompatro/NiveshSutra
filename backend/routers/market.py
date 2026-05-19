from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict
from backend.models.db_models import Stock, Ohlcv
from ..services.market_data import get_quote_with_fallback

router = APIRouter()


@router.get("/market/overview")
async def market_overview(db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.active == True).all()
    overview = []
    for stock in stocks:
        bars = (
            db.query(Ohlcv)
            .filter(Ohlcv.symbol == stock.symbol)
            .order_by(Ohlcv.date.desc())
            .limit(2)
            .all()
        )
        if bars and len(bars) >= 2:
            current = float(bars[0].close)
            previous = float(bars[1].close)
            change_pct = ((current - previous) / previous) * 100
            overview.append({
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "price": current,
                "change_pct": round(change_pct, 2),
                "date": bars[0].date,
            })
    overview.sort(key=lambda x: x.get("change_pct", 0), reverse=True)
    return overview


@router.get("/market/index-overview")
async def market_index_overview(db: Session = Depends(get_db)):
    try:
        quote = get_quote_with_fallback(db, "^NSEI")
        return {
            "nifty50_value": quote.price,
            "nifty50_change": quote.change,
            "nifty50_change_pct": quote.change_pct,
            "provider": quote.provider,
        }
    except Exception:
        bars = (
            db.query(Ohlcv)
            .filter(Ohlcv.symbol == "^NSEI")
            .order_by(Ohlcv.date.desc())
            .limit(2)
            .all()
        )
        if not bars:
            return None

        latest = float(bars[0].close)
        previous = float(bars[1].close) if len(bars) > 1 else latest
        change = latest - previous
        change_pct = (change / previous * 100) if previous else 0
        return {
            "nifty50_value": latest,
            "nifty50_change": change,
            "nifty50_change_pct": change_pct,
            "provider": "database",
        }
