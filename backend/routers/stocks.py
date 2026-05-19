from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict
from backend.models.db_models import Stock, Ohlcv, Signal, TechnicalIndicator

from ..services.market_data import (
    fetch_historical_daily,
    fetch_live_quotes_batch,
    get_quote_with_fallback,
    merge_live_quote_into_history,
)
from ..validation import require_stock_symbol

router = APIRouter()


@router.get("/stocks")
async def list_stocks(
    sector: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Stock).filter(Stock.active == True)
    if sector:
        query = query.filter(Stock.sector == sector)
    stocks = query.order_by(Stock.symbol).all()
    return [row_to_dict(s) for s in stocks]


@router.get("/stocks/live")
async def list_stocks_live(
    sector: str | None = None,
    nifty50_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Stock).filter(Stock.active == True)
    if sector:
        query = query.filter(Stock.sector == sector)
    if nifty50_only:
        query = query.filter(Stock.is_nifty50 == True)
    stocks = query.order_by(Stock.symbol).all()

    signals = (
        db.query(Signal.symbol, Signal.signal, Signal.date)
        .order_by(Signal.date.desc())
        .limit(max(50, len(stocks) * 2))
        .all()
    )
    signal_map: dict[str, str] = {}
    for row in signals:
        signal_map.setdefault(row.symbol, row.signal)

    quote_map = fetch_live_quotes_batch(
        {stock.symbol: stock.yf_ticker for stock in stocks}
    )

    enriched = []
    for stock in stocks:
        quote = quote_map.get(stock.symbol) or get_quote_with_fallback(
            db, stock.symbol, stock.yf_ticker
        )
        enriched.append(
            {
                "symbol": stock.symbol,
                "company_name": stock.company_name or "",
                "sector": stock.sector or "",
                "current_price": quote.price,
                "previous_close": quote.previous_close,
                "change": quote.change,
                "change_pct": quote.change_pct,
                "signal": signal_map.get(stock.symbol),
                "provider": quote.provider,
                "latest_trading_day": quote.latest_trading_day,
            }
        )
    return enriched


@router.get("/stocks/{symbol}")
async def get_stock(symbol: str, db: Session = Depends(get_db)):
    symbol = require_stock_symbol(symbol)
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return row_to_dict(stock)


@router.get("/stocks/{symbol}/quote")
async def get_stock_quote(symbol: str, db: Session = Depends(get_db)):
    symbol = require_stock_symbol(symbol)
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
    if not stock:
        return None

    quote = get_quote_with_fallback(db, symbol, stock.yf_ticker)
    return {
        "symbol": stock.symbol,
        "company_name": stock.company_name or "",
        "sector": stock.sector or "",
        "current_price": quote.price,
        "change_pct": quote.change_pct,
        "change": quote.change,
        "day_high": quote.high,
        "day_low": quote.low,
        "volume": quote.volume,
        "market_cap": 0,
        "provider": quote.provider,
        "latest_trading_day": quote.latest_trading_day,
    }


@router.get("/stocks/{symbol}/ohlcv")
async def get_ohlcv(
    symbol: str,
    days: int = Query(default=90, ge=1, le=3650),
    db: Session = Depends(get_db),
):
    symbol = require_stock_symbol(symbol)
    db_rows = (
        db.query(Ohlcv)
        .filter(Ohlcv.symbol == symbol)
        .order_by(Ohlcv.date.desc())
        .limit(days)
        .all()
    )
    rows = sorted(
        [row_to_dict(r) for r in db_rows],
        key=lambda x: x["date"],
    )
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        ticker = stock.yf_ticker if stock else None
        live_history = fetch_historical_daily(symbol, ticker, days)
        if live_history:
            rows = live_history
        quote = get_quote_with_fallback(db, symbol, ticker)
        rows = merge_live_quote_into_history(rows, quote)
    except Exception:
        pass
    return rows


@router.get("/stocks/{symbol}/indicators")
async def get_indicators(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    symbol = require_stock_symbol(symbol)
    db_rows = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.symbol == symbol)
        .order_by(TechnicalIndicator.date.desc())
        .limit(days)
        .all()
    )
    result = [row_to_dict(r) for r in db_rows]
    return sorted(result, key=lambda x: x["date"])
