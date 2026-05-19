from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from backend.database import get_db, row_to_dict
from backend.models.db_models import SentimentDaily, ArticleSentiment, NewsArticle

router = APIRouter()


@router.get("/stocks/{symbol}/sentiment")
async def get_sentiment(
    symbol: str,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(SentimentDaily)
        .filter(SentimentDaily.symbol == symbol)
        .order_by(SentimentDaily.date.desc())
        .limit(days)
        .all()
    )
    result = [row_to_dict(r) for r in rows]
    return sorted(result, key=lambda x: x["date"])


@router.get("/stocks/{symbol}/news")
async def get_news(
    symbol: str,
    limit: int = Query(default=20, le=50),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ArticleSentiment)
        .options(joinedload(ArticleSentiment.article))
        .filter(ArticleSentiment.symbol == symbol)
        .order_by(ArticleSentiment.computed_at.desc())
        .limit(limit)
        .all()
    )
    return [row_to_dict(r, rels=["article"]) for r in rows]


@router.get("/sentiment/market")
async def market_sentiment(db: Session = Depends(get_db)):
    rows = (
        db.query(SentimentDaily)
        .order_by(SentimentDaily.date.desc())
        .limit(50)
        .all()
    )
    data = [row_to_dict(r) for r in rows]
    if not data:
        return {"overall": 0, "stocks": []}

    latest_date = data[0]["date"]
    today_data = [r for r in data if r["date"] == latest_date]
    avg = sum(float(r["avg_sentiment"]) for r in today_data) / len(today_data) if today_data else 0
    return {"overall": round(avg, 3), "date": latest_date, "stocks": today_data}
