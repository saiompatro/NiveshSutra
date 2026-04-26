from fastapi import APIRouter, Depends, Query
from supabase import Client
from ..dependencies import get_supabase_client

router = APIRouter()


@router.get("/stocks/{symbol}/sentiment")
async def get_sentiment(
    symbol: str,
    days: int = Query(default=30, le=90),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("sentiment_daily")
        .select("*")
        .eq("symbol", symbol)
        .order("date", desc=True)
        .limit(days)
        .execute()
    )
    return sorted(result.data, key=lambda x: x["date"])


@router.get("/stocks/{symbol}/news")
async def get_news(
    symbol: str,
    limit: int = Query(default=20, le=50),
    supabase: Client = Depends(get_supabase_client),
):
    result = (
        supabase.table("article_sentiments")
        .select("*, news_articles(*)")
        .eq("symbol", symbol)
        .order("computed_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


@router.get("/sentiment/market")
async def market_sentiment(supabase: Client = Depends(get_supabase_client)):
    result = (
        supabase.table("sentiment_daily")
        .select("symbol, avg_sentiment, article_count, date")
        .order("date", desc=True)
        .limit(50)
        .execute()
    )
    if not result.data:
        return {"overall": 0, "stocks": []}

    latest_date = result.data[0]["date"]
    today_data = [r for r in result.data if r["date"] == latest_date]
    avg = sum(float(r["avg_sentiment"]) for r in today_data) / len(today_data) if today_data else 0
    return {"overall": round(avg, 3), "date": latest_date, "stocks": today_data}
