"""
Upsert OHLCV, indicator, news, sentiment, and signal data to SQLite via SQLAlchemy.
Batches in chunks of 500 rows with ON CONFLICT upserts.
"""

import math
import pandas as pd

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.database import SessionLocal
from backend.models.db_models import (
    Ohlcv, TechnicalIndicator, NewsArticle, ArticleSentiment,
    SentimentDaily, Signal,
)

BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Generic bulk-upsert helper
# ---------------------------------------------------------------------------

def _bulk_upsert(session, model, records, conflict_cols, update_cols):
    """Bulk upsert records into a table."""
    if not records:
        return
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        stmt = sqlite_insert(model.__table__).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={col: stmt.excluded[col] for col in update_cols},
        )
        session.execute(stmt)
    session.commit()


# ---------------------------------------------------------------------------
# Upsert functions
# ---------------------------------------------------------------------------

def upsert_ohlcv(df: pd.DataFrame, session=None) -> int:
    if df.empty:
        print("No OHLCV data to upsert.")
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        records = _df_to_records(df)
        total = len(records)

        num_batches = math.ceil(total / BATCH_SIZE)
        print(f"Upserting {total} OHLCV rows in {num_batches} batches...")

        _bulk_upsert(
            session, Ohlcv, records,
            conflict_cols=["symbol", "date"],
            update_cols=["open", "high", "low", "close", "adj_close", "volume"],
        )

        print(f"Upserted {total} OHLCV rows.")
        return total
    finally:
        if own_session:
            session.close()


def upsert_indicators(df: pd.DataFrame, session=None) -> int:
    if df.empty:
        print("No indicator data to upsert.")
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        records = _df_to_records(df)
        total = len(records)

        num_batches = math.ceil(total / BATCH_SIZE)
        print(f"Upserting {total} indicator rows in {num_batches} batches...")

        _bulk_upsert(
            session, TechnicalIndicator, records,
            conflict_cols=["symbol", "date"],
            update_cols=[
                "rsi_14", "macd_line", "macd_signal", "macd_hist",
                "bb_upper", "bb_middle", "bb_lower",
                "sma_20", "sma_50", "ema_12", "ema_26",
                "atr_14", "obv",
            ],
        )

        print(f"Upserted {total} indicator rows.")
        return total
    finally:
        if own_session:
            session.close()


def upsert_news_articles(articles: list[dict], session=None) -> int:
    if not articles:
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        _bulk_upsert(
            session, NewsArticle, articles,
            conflict_cols=["url"],
            update_cols=["title", "source", "published_at"],
        )

        total = len(articles)
        print(f"Upserted {total} news articles.")
        return total
    finally:
        if own_session:
            session.close()


def upsert_article_sentiments(sentiments: list[dict], session=None) -> int:
    if not sentiments:
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        _bulk_upsert(
            session, ArticleSentiment, sentiments,
            conflict_cols=["article_id", "symbol"],
            update_cols=[
                "positive_prob", "negative_prob", "neutral_prob",
                "sentiment_label", "relevance_score", "computed_at",
            ],
        )

        total = len(sentiments)
        print(f"Upserted {total} article sentiments.")
        return total
    finally:
        if own_session:
            session.close()


def upsert_daily_sentiment(records_list: list[dict], session=None) -> int:
    if not records_list:
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        _bulk_upsert(
            session, SentimentDaily, records_list,
            conflict_cols=["symbol", "date"],
            update_cols=[
                "avg_sentiment", "positive_avg", "negative_avg",
                "neutral_avg", "article_count",
            ],
        )

        total = len(records_list)
        print(f"Upserted {total} daily sentiment rows.")
        return total
    finally:
        if own_session:
            session.close()


def upsert_signals(signals: list[dict], session=None) -> int:
    if not signals:
        return 0

    own_session = session is None
    if own_session:
        session = SessionLocal()

    try:
        _bulk_upsert(
            session, Signal, signals,
            conflict_cols=["symbol", "date"],
            update_cols=[
                "technical_score", "sentiment_score", "momentum_score",
                "composite_score", "signal", "confidence", "explanation",
            ],
        )

        total = len(signals)
        print(f"Upserted {total} signal rows.")
        return total
    finally:
        if own_session:
            session.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts, replacing NaN with None."""
    records = df.where(pd.notna(df), None).to_dict(orient="records")
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                rec[k] = None
            elif k == "obv" and v is not None:
                rec[k] = int(v)
    return records
