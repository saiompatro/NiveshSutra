from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID
from backend.models.db_models import Watchlist, Stock
from ..services.market_data import fetch_live_quotes_batch, get_quote_with_fallback

router = APIRouter()


@router.get("/watchlist")
async def get_watchlist(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    items = (
        db.query(Watchlist)
        .options(joinedload(Watchlist.stock))
        .filter(Watchlist.user_id == user_id)
        .order_by(Watchlist.added_at.desc())
        .all()
    )
    return [row_to_dict(w, rels=["stock"]) for w in items]


@router.get("/watchlist/live")
async def get_watchlist_live(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    items = (
        db.query(Watchlist)
        .options(joinedload(Watchlist.stock))
        .filter(Watchlist.user_id == user_id)
        .order_by(Watchlist.added_at.desc())
        .all()
    )

    quote_map = fetch_live_quotes_batch(
        {
            w.symbol: (w.stock.yf_ticker if w.stock else None)
            for w in items
        }
    )

    result = []
    for w in items:
        yf_ticker = w.stock.yf_ticker if w.stock else None
        quote = quote_map.get(w.symbol) or get_quote_with_fallback(
            db, w.symbol, yf_ticker
        )
        result.append(
            {
                "symbol": w.symbol,
                "company_name": (w.stock.company_name if w.stock else "") or "",
                "current_price": quote.price,
                "previous_close": quote.previous_close,
                "change": quote.change,
                "change_pct": quote.change_pct,
                "provider": quote.provider,
            }
        )
    return result


@router.post("/watchlist/{symbol}")
async def add_to_watchlist(symbol: str, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    existing = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user_id, Watchlist.symbol == symbol)
        .first()
    )
    if existing:
        return row_to_dict(existing)
    item = Watchlist(user_id=user_id, symbol=symbol)
    db.add(item)
    db.commit()
    db.refresh(item)
    return row_to_dict(item)


@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    item = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == user_id, Watchlist.symbol == symbol)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return {"status": "removed"}
