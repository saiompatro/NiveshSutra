from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db, row_to_dict
from backend.models.db_models import Signal

router = APIRouter()


@router.get("/signals")
async def list_signals(
    signal_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Signal).order_by(Signal.date.desc()).limit(50)
    if signal_type:
        query = query.filter(Signal.signal == signal_type)
    rows = query.all()

    # Deduplicate to latest per symbol
    seen = set()
    latest = []
    for row in rows:
        d = row_to_dict(row)
        if d["symbol"] not in seen:
            seen.add(d["symbol"])
            latest.append(d)
    return latest


@router.get("/signals/summary")
async def signals_summary(db: Session = Depends(get_db)):
    rows = (
        db.query(Signal.symbol, Signal.signal, Signal.date)
        .order_by(Signal.date.desc())
        .limit(200)
        .all()
    )
    seen = {}
    for row in rows:
        if row.symbol not in seen:
            seen[row.symbol] = row.signal
    counts = {}
    for signal in seen.values():
        counts[signal] = counts.get(signal, 0) + 1
    return {"counts": counts, "total": len(seen)}


@router.get("/signals/{symbol}")
async def get_signal_history(
    symbol: str,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Signal)
        .filter(Signal.symbol == symbol)
        .order_by(Signal.date.desc())
        .limit(days)
        .all()
    )
    result = [row_to_dict(r) for r in rows]
    return sorted(result, key=lambda x: x["date"])


@router.get("/signals/{symbol}/latest")
async def get_latest_signal(symbol: str, db: Session = Depends(get_db)):
    row = (
        db.query(Signal)
        .filter(Signal.symbol == symbol)
        .order_by(Signal.date.desc())
        .first()
    )
    return row_to_dict(row) if row else None
