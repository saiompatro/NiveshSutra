"""
Upsert OHLCV and indicator data to Supabase.
Batches in chunks of 500 rows with on_conflict for (symbol, date).
"""

import math
import pandas as pd

from services.ml.config import get_supabase

BATCH_SIZE = 500


def upsert_ohlcv(df: pd.DataFrame) -> int:
    """
    Upsert OHLCV rows to Supabase ohlcv table.

    Args:
        df: DataFrame with columns matching the ohlcv table.

    Returns:
        Number of rows upserted.
    """
    if df.empty:
        print("No OHLCV data to upsert.")
        return 0

    sb = get_supabase()
    records = _df_to_records(df)
    total = 0

    num_batches = math.ceil(len(records) / BATCH_SIZE)
    print(f"Upserting {len(records)} OHLCV rows in {num_batches} batches...")

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        sb.table("ohlcv").upsert(batch, on_conflict="symbol,date").execute()
        total += len(batch)
        batch_num = (i // BATCH_SIZE) + 1
        if batch_num % 5 == 0 or batch_num == num_batches:
            print(f"  OHLCV batch {batch_num}/{num_batches} done ({total} rows)")

    print(f"Upserted {total} OHLCV rows.")
    return total


def upsert_indicators(df: pd.DataFrame) -> int:
    """
    Upsert indicator rows to Supabase technical_indicators table.

    Args:
        df: DataFrame with columns matching the technical_indicators table.

    Returns:
        Number of rows upserted.
    """
    if df.empty:
        print("No indicator data to upsert.")
        return 0

    sb = get_supabase()
    records = _df_to_records(df)
    total = 0

    num_batches = math.ceil(len(records) / BATCH_SIZE)
    print(f"Upserting {len(records)} indicator rows in {num_batches} batches...")

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        sb.table("technical_indicators").upsert(batch, on_conflict="symbol,date").execute()
        total += len(batch)
        batch_num = (i // BATCH_SIZE) + 1
        if batch_num % 5 == 0 or batch_num == num_batches:
            print(f"  Indicators batch {batch_num}/{num_batches} done ({total} rows)")

    print(f"Upserted {total} indicator rows.")
    return total


def upsert_news_articles(articles: list[dict]) -> int:
    """Upsert news articles to Supabase news_articles table."""
    if not articles:
        return 0

    sb = get_supabase()
    total = 0

    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i : i + BATCH_SIZE]
        sb.table("news_articles").upsert(batch, on_conflict="url").execute()
        total += len(batch)

    print(f"Upserted {total} news articles.")
    return total


def upsert_article_sentiments(sentiments: list[dict]) -> int:
    """Upsert article sentiments to Supabase article_sentiments table."""
    if not sentiments:
        return 0

    sb = get_supabase()
    total = 0

    for i in range(0, len(sentiments), BATCH_SIZE):
        batch = sentiments[i : i + BATCH_SIZE]
        sb.table("article_sentiments").upsert(
            batch, on_conflict="article_id,symbol"
        ).execute()
        total += len(batch)

    print(f"Upserted {total} article sentiments.")
    return total


def upsert_daily_sentiment(records_list: list[dict]) -> int:
    """Upsert daily aggregated sentiment to Supabase sentiment_daily table."""
    if not records_list:
        return 0

    sb = get_supabase()
    total = 0

    for i in range(0, len(records_list), BATCH_SIZE):
        batch = records_list[i : i + BATCH_SIZE]
        sb.table("sentiment_daily").upsert(
            batch, on_conflict="symbol,date"
        ).execute()
        total += len(batch)

    print(f"Upserted {total} daily sentiment rows.")
    return total


def upsert_signals(signals: list[dict]) -> int:
    """Upsert signals to Supabase signals table."""
    if not signals:
        return 0

    sb = get_supabase()
    total = 0

    for i in range(0, len(signals), BATCH_SIZE):
        batch = signals[i : i + BATCH_SIZE]
        sb.table("signals").upsert(batch, on_conflict="symbol,date").execute()
        total += len(batch)

    print(f"Upserted {total} signal rows.")
    return total


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts, replacing NaN with None."""
    records = df.where(pd.notna(df), None).to_dict(orient="records")
    # Ensure None values are JSON-serializable (not float nan)
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                rec[k] = None
    return records
