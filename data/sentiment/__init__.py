"""
Sentiment analysis pipeline:
  1. Fetch Moneycontrol news via moneycontrol-api
  2. Map articles to Nifty 50 stock symbols
  3. Score headlines with ProsusAI/finbert
  4. Aggregate daily sentiment per symbol
  5. Persist everything to Supabase
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Nifty 50 ticker mapper  (company name / alias -> symbol)
# All patterns are lowercased at lookup time.
# ---------------------------------------------------------------------------
TICKER_MAP: dict[str, str] = {
    # Adani group
    "adani enterprises": "ADANIENT",
    "adani ports": "ADANIPORTS",
    "adani ports and sez": "ADANIPORTS",
    # Apollo
    "apollo hospitals": "APOLLOHOSP",
    "apollo hospital": "APOLLOHOSP",
    # Asian Paints
    "asian paints": "ASIANPAINT",
    "asian paint": "ASIANPAINT",
    # Axis Bank
    "axis bank": "AXISBANK",
    "axis": "AXISBANK",
    # Bajaj
    "bajaj auto": "BAJAJ-AUTO",
    "bajaj finance": "BAJFINANCE",
    "bajaj finserv": "BAJAJFINSV",
    # Bharti Airtel
    "bharti airtel": "BHARTIARTL",
    "airtel": "BHARTIARTL",
    # BPCL
    "bpcl": "BPCL",
    "bharat petroleum": "BPCL",
    # Britannia
    "britannia": "BRITANNIA",
    "britannia industries": "BRITANNIA",
    # Cipla
    "cipla": "CIPLA",
    # Coal India
    "coal india": "COALINDIA",
    # Divis Labs
    "divi's lab": "DIVISLAB",
    "divis lab": "DIVISLAB",
    "divi's laboratories": "DIVISLAB",
    # Dr Reddy's
    "dr reddy": "DRREDDY",
    "dr. reddy": "DRREDDY",
    "dr reddy's": "DRREDDY",
    # Eicher Motors
    "eicher motors": "EICHERMOT",
    "eicher": "EICHERMOT",
    "royal enfield": "EICHERMOT",
    # Grasim
    "grasim": "GRASIM",
    "grasim industries": "GRASIM",
    # HCL Tech
    "hcl tech": "HCLTECH",
    "hcl technologies": "HCLTECH",
    # HDFC Bank
    "hdfc bank": "HDFCBANK",
    "hdfc": "HDFCBANK",
    # HDFC Life
    "hdfc life": "HDFCLIFE",
    # Hero Motocorp
    "hero motocorp": "HEROMOTOCO",
    "hero moto": "HEROMOTOCO",
    # Hindalco
    "hindalco": "HINDALCO",
    "hindalco industries": "HINDALCO",
    # HUL
    "hindustan unilever": "HINDUNILVR",
    "hul": "HINDUNILVR",
    # ICICI Bank
    "icici bank": "ICICIBANK",
    "icici": "ICICIBANK",
    # IndusInd Bank
    "indusind bank": "INDUSINDBK",
    "indusind": "INDUSINDBK",
    # Infosys
    "infosys": "INFY",
    "infy": "INFY",
    # ITC
    "itc": "ITC",
    # JSW Steel
    "jsw steel": "JSWSTEEL",
    "jsw": "JSWSTEEL",
    # Kotak Mahindra
    "kotak mahindra": "KOTAKBANK",
    "kotak bank": "KOTAKBANK",
    "kotak": "KOTAKBANK",
    # L&T
    "larsen & toubro": "LT",
    "larsen and toubro": "LT",
    "l&t": "LT",
    # LTIMindtree
    "ltimindtree": "LTIM",
    "lti mindtree": "LTIM",
    # M&M
    "mahindra & mahindra": "M&M",
    "mahindra and mahindra": "M&M",
    "m&m": "M&M",
    "mahindra": "M&M",
    # Maruti Suzuki
    "maruti suzuki": "MARUTI",
    "maruti": "MARUTI",
    # Nestle
    "nestle india": "NESTLEIND",
    "nestle": "NESTLEIND",
    # NTPC
    "ntpc": "NTPC",
    # ONGC
    "ongc": "ONGC",
    "oil and natural gas": "ONGC",
    # Power Grid
    "power grid": "POWERGRID",
    "power grid corporation": "POWERGRID",
    # Reliance
    "reliance industries": "RELIANCE",
    "reliance": "RELIANCE",
    "ril": "RELIANCE",
    # SBI
    "state bank of india": "SBIN",
    "sbi": "SBIN",
    "sbin": "SBIN",
    # SBI Life
    "sbi life": "SBILIFE",
    # Sun Pharma
    "sun pharma": "SUNPHARMA",
    "sun pharmaceutical": "SUNPHARMA",
    # Tata Consumer
    "tata consumer": "TATACONSUM",
    "tata consumer products": "TATACONSUM",
    # Tata Motors
    "tata motors": "TATAMOTORS",
    # Tata Steel
    "tata steel": "TATASTEEL",
    # TCS
    "tata consultancy": "TCS",
    "tata consultancy services": "TCS",
    "tcs": "TCS",
    # Tech Mahindra
    "tech mahindra": "TECHM",
    # Titan
    "titan": "TITAN",
    "titan company": "TITAN",
    # Trent
    "trent": "TRENT",
    "trent limited": "TRENT",
    # UltraTech
    "ultratech": "ULTRACEMCO",
    "ultratech cement": "ULTRACEMCO",
    # Wipro
    "wipro": "WIPRO",
}

# Pre-compile patterns sorted longest-first so longer names match first
_PATTERNS: list[tuple[re.Pattern, str]] = sorted(
    [
        (re.compile(r"\b" + re.escape(alias) + r"\b", re.IGNORECASE), symbol)
        for alias, symbol in TICKER_MAP.items()
    ],
    key=lambda t: -len(t[0].pattern),
)

# ---------------------------------------------------------------------------
# FinBERT singleton
# ---------------------------------------------------------------------------
_finbert_pipeline = None


def _get_finbert():
    """Lazy-load ProsusAI/finbert as a singleton."""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        from transformers import pipeline

        print("Loading FinBERT model (first call only)...")
        _finbert_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            top_k=3,
        )
    return _finbert_pipeline


# ---------------------------------------------------------------------------
# 1. Fetch news
# ---------------------------------------------------------------------------


_IST = timezone(timedelta(hours=5, minutes=30))


def _parse_moneycontrol_datetime(value: str | None, fallback: str) -> str:
    if not value:
        return fallback

    cleaned = re.sub(r"\s+", " ", value).strip()
    formats = (
        "%B %d, %Y %I:%M %p",
        "%b %d, %Y %I:%M %p",
        "%d %b %Y %I:%M %p",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.replace(tzinfo=_IST).astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return fallback


def _normalize_news_item(item: Any, source_label: str, fetched_at: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    url = item.get("Link:") or item.get("Link") or item.get("link") or item.get("url")
    title = item.get("Title:") or item.get("Title") or item.get("title") or ""
    if not url or not title:
        return None

    published_raw = item.get("Date:") or item.get("Date") or item.get("date")
    news_type = (
        item.get("NewsType:")
        or item.get("NewsType")
        or item.get("news_type")
        or source_label
    )
    return {
        "url": str(url).strip(),
        "title": str(title).strip(),
        "source": f"moneycontrol:{news_type}".lower(),
        "published_at": _parse_moneycontrol_datetime(
            str(published_raw).strip() if published_raw else None,
            fetched_at,
        ),
        "fetched_at": fetched_at,
    }


def _iter_moneycontrol_results(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if all(not isinstance(value, (dict, list)) for value in payload.values()):
            return [payload]
        results: list[dict[str, Any]] = []
        for value in payload.values():
            results.extend(_iter_moneycontrol_results(value))
        return results
    return []


def fetch_news() -> list[dict[str, Any]]:
    """
    Fetch articles from Moneycontrol via moneycontrol-api.

    Returns:
        list of dicts with keys: url, title, source, published_at, fetched_at
    """
    now = datetime.now(timezone.utc).isoformat()
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []

    try:
        from moneycontrol import moneycontrol_api as mc
    except ImportError as exc:
        raise RuntimeError(
            "moneycontrol-api is not installed. Add it to the environment before running sentiment ingestion."
        ) from exc

    sources = (
        ("get_latest_news", "latest_news"),
        ("get_business_news", "business_news"),
        ("get_news", "news"),
    )
    for func_name, source_label in sources:
        func = getattr(mc, func_name, None)
        if not callable(func):
            print(f"Warning: moneycontrol-api does not expose {func_name}()")
            continue

        try:
            payload = func()
        except Exception as exc:
            print(f"Warning: Moneycontrol fetch failed for {func_name}: {exc}")
            continue

        for item in _iter_moneycontrol_results(payload):
            article = _normalize_news_item(item, source_label, now)
            if not article or article["url"] in seen_urls:
                continue
            seen_urls.add(article["url"])
            articles.append(article)

    print(f"Fetched {len(articles)} unique articles from Moneycontrol.")
    return articles


# ---------------------------------------------------------------------------
# 2. Map articles to symbols
# ---------------------------------------------------------------------------


def map_articles_to_symbols(articles: list[dict]) -> list[dict]:
    """
    Map articles to stock symbols by scanning titles for company names/aliases.

    Returns:
        list of dicts with keys: article_id, symbol, relevance_score
    """
    mappings: list[dict] = []
    for article in articles:
        title = article.get("title", "")
        article_id = article.get("id")
        matched_symbols: set[str] = set()
        for pattern, symbol in _PATTERNS:
            if pattern.search(title):
                matched_symbols.add(symbol)
        for symbol in matched_symbols:
            mappings.append(
                {
                    "article_id": article_id,
                    "symbol": symbol,
                    "relevance_score": (
                        1.0
                        if len(matched_symbols) == 1
                        else round(1.0 / len(matched_symbols), 4)
                    ),
                }
            )
    print(
        f"Mapped {len(mappings)} article-symbol pairs from {len(articles)} articles."
    )
    return mappings


# ---------------------------------------------------------------------------
# 3. Score sentiments with FinBERT
# ---------------------------------------------------------------------------


def score_sentiments(articles: list[dict]) -> list[dict]:
    """
    Run FinBERT on article titles and return per-article per-symbol sentiment scores.

    Expects articles to already have 'id' and '_symbols' (set of matched symbols)
    populated.

    Returns:
        list of dicts with keys:
            article_id, symbol, positive_prob, negative_prob, neutral_prob,
            sentiment_label, relevance_score, computed_at
    """
    finbert = _get_finbert()
    now = datetime.now(timezone.utc).isoformat()

    # Collect articles that have symbol mappings
    scoreable = [(a, a["_symbols"]) for a in articles if a.get("_symbols")]
    if not scoreable:
        print("No articles matched any symbols; nothing to score.")
        return []

    titles = [a["title"] for a, _ in scoreable]

    # Batch inference
    print(f"Running FinBERT on {len(titles)} headlines...")
    results = finbert(titles, batch_size=32, truncation=True, max_length=512)

    sentiments: list[dict] = []
    for (article, symbols), preds in zip(scoreable, results):
        probs = {p["label"]: round(p["score"], 6) for p in preds}
        pos = probs.get("positive", 0.0)
        neg = probs.get("negative", 0.0)
        neu = probs.get("neutral", 0.0)
        label = max(probs, key=probs.get)  # type: ignore[arg-type]

        # sentiment_score: positive - negative, in [-1, +1]
        sent_score = round(pos - neg, 6)
        for sym in symbols:
            sentiments.append(
                {
                    "article_id": article["id"],
                    "symbol": sym,
                    "positive_prob": pos,
                    "negative_prob": neg,
                    "neutral_prob": neu,
                    "sentiment_label": label,
                    "sentiment_score": sent_score,
                    "computed_at": now,
                }
            )

    print(f"Scored {len(sentiments)} article-symbol sentiment rows.")
    return sentiments


# ---------------------------------------------------------------------------
# 4. Aggregate daily sentiment
# ---------------------------------------------------------------------------


def aggregate_daily(sentiments: list[dict]) -> list[dict]:
    """
    Aggregate per-article sentiments into daily sentiment per symbol.

    Returns:
        list of dicts with keys:
            symbol, date, avg_sentiment, positive_avg, negative_avg,
            neutral_avg, article_count
    """
    from collections import defaultdict

    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)

    today_str = date.today().isoformat()
    for s in sentiments:
        key = (s["symbol"], today_str)
        buckets[key].append(s)

    daily: list[dict] = []
    for (symbol, day), rows in buckets.items():
        n = len(rows)
        pos_avg = sum(r["positive_prob"] for r in rows) / n
        neg_avg = sum(r["negative_prob"] for r in rows) / n
        neu_avg = sum(r["neutral_prob"] for r in rows) / n
        avg_sentiment = round(pos_avg - neg_avg, 6)
        daily.append(
            {
                "symbol": symbol,
                "date": day,
                "avg_sentiment": avg_sentiment,
                "positive_avg": round(pos_avg, 6),
                "negative_avg": round(neg_avg, 6),
                "neutral_avg": round(neu_avg, 6),
                "article_count": n,
            }
        )

    print(f"Aggregated daily sentiment for {len(daily)} symbol-date pairs.")
    return daily


# ---------------------------------------------------------------------------
# 5. Orchestrator
# ---------------------------------------------------------------------------


def run_sentiment_pipeline() -> None:
    """Run the full sentiment pipeline end-to-end."""
    import time

    from data.ingest.store import (
        upsert_news_articles,
        upsert_article_sentiments,
        upsert_daily_sentiment,
    )

    start = time.time()

    # --- fetch ---
    print("=" * 60)
    print("SENTIMENT STEP 1: Fetching Moneycontrol news")
    print("=" * 60)
    articles = fetch_news()
    if not articles:
        print("No articles fetched. Exiting pipeline.")
        return

    # --- store articles and get back IDs ---
    print()
    print("=" * 60)
    print("SENTIMENT STEP 2: Storing articles in Supabase")
    print("=" * 60)
    upsert_news_articles(articles)

    # Retrieve article IDs from Supabase (using url as key)
    from data.config import get_supabase

    sb = get_supabase()
    urls = [a["url"] for a in articles]
    # Fetch in batches to avoid query-string size limits
    article_id_map: dict[str, str] = {}
    batch_size = 50
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i : i + batch_size]
        resp = (
            sb.table("news_articles")
            .select("id,url")
            .in_("url", batch_urls)
            .execute()
        )
        for row in resp.data:
            article_id_map[row["url"]] = row["id"]

    # Enrich articles with DB IDs and symbol mappings
    for a in articles:
        a["id"] = article_id_map.get(a["url"])

    # --- map to symbols ---
    print()
    print("=" * 60)
    print("SENTIMENT STEP 3: Mapping articles to stock symbols")
    print("=" * 60)
    # Attach symbol sets to articles
    for a in articles:
        title = a.get("title", "")
        matched: set[str] = set()
        for pattern, symbol in _PATTERNS:
            if pattern.search(title):
                matched.add(symbol)
        a["_symbols"] = matched

    # --- score ---
    print()
    print("=" * 60)
    print("SENTIMENT STEP 4: Scoring with FinBERT")
    print("=" * 60)
    sentiments = score_sentiments(articles)

    if not sentiments:
        print("No sentiments produced. Exiting.")
        return

    # --- store article sentiments ---
    print()
    print("=" * 60)
    print("SENTIMENT STEP 5: Storing article sentiments")
    print("=" * 60)
    upsert_article_sentiments(sentiments)

    # --- aggregate ---
    print()
    print("=" * 60)
    print("SENTIMENT STEP 6: Aggregating daily sentiment")
    print("=" * 60)
    daily = aggregate_daily(sentiments)
    upsert_daily_sentiment(daily)

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"SENTIMENT PIPELINE DONE in {elapsed:.1f}s")
    print(f"  Articles fetched:   {len(articles)}")
    print(f"  Sentiments scored:  {len(sentiments)}")
    print(f"  Daily aggregations: {len(daily)}")
    print("=" * 60)
