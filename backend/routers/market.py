from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.db_models import Stock, Ohlcv
from ..services.market_data import get_latest_db_bars, get_quote_with_fallback, quote_from_db_bars

router = APIRouter()


@router.get("/market/overview")
async def market_overview(db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.active == True).all()
    db_bars = get_latest_db_bars(db, [stock.symbol for stock in stocks])
    overview = []
    for stock in stocks:
        quote = quote_from_db_bars(stock.symbol, db_bars.get(stock.symbol, []))
        if quote:
            overview.append({
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "price": quote.price,
                "change_pct": round(quote.change_pct, 2),
                "date": quote.latest_trading_day,
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
