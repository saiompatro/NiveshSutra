from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db, row_to_dict, DEFAULT_USER_ID
from backend.models.db_models import Holding, Stock
from ..models.holding import HoldingCreate, HoldingUpdate
from ..services.market_data import fetch_live_quotes_batch, get_quote_with_fallback

router = APIRouter()


@router.get("/holdings")
async def list_holdings(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    holdings = (
        db.query(Holding)
        .options(joinedload(Holding.stock))
        .filter(Holding.user_id == user_id)
        .order_by(Holding.created_at.desc())
        .all()
    )
    return [row_to_dict(h, rels=["stock"]) for h in holdings]


@router.get("/holdings/live")
async def list_holdings_live(db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    holdings = (
        db.query(Holding)
        .options(joinedload(Holding.stock))
        .filter(Holding.user_id == user_id)
        .all()
    )

    quote_map = fetch_live_quotes_batch(
        {
            h.symbol: (h.stock.yf_ticker if h.stock else None)
            for h in holdings
        }
    )

    enriched = []
    for h in holdings:
        yf_ticker = h.stock.yf_ticker if h.stock else None
        quote = quote_map.get(h.symbol) or get_quote_with_fallback(
            db, h.symbol, yf_ticker
        )
        avg_price = float(h.avg_buy_price or 0)
        quantity = float(h.quantity or 0)
        value = quote.price * quantity
        invested = avg_price * quantity
        pnl = value - invested
        pnl_pct = (pnl / invested * 100) if invested else 0
        enriched.append(
            {
                "id": h.id,
                "symbol": h.symbol,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": quote.price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "value": value,
                "provider": quote.provider,
            }
        )
    return enriched


@router.post("/holdings")
async def create_holding(body: HoldingCreate, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    data = body.model_dump()
    h = Holding(user_id=user_id, **data)
    db.add(h)
    db.commit()
    db.refresh(h)
    return row_to_dict(h)


@router.put("/holdings/{holding_id}")
async def update_holding(holding_id: str, body: HoldingUpdate, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    h = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user_id).first()
    if not h:
        return None
    data = body.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(h, key, value)
    db.commit()
    db.refresh(h)
    return row_to_dict(h)


@router.delete("/holdings/{holding_id}")
async def delete_holding(holding_id: str, db: Session = Depends(get_db)):
    user_id = DEFAULT_USER_ID
    h = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user_id).first()
    if h:
        db.delete(h)
        db.commit()
    return {"status": "deleted"}
