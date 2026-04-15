"""
Sentiment analysis pipeline:
  1. Fetch news via RSS (Moneycontrol, Economic Times)
  2. Map articles to Nifty 50 stock symbols
  3. Score headlines with ProsusAI/finbert
  4. Aggregate daily sentiment per symbol
  5. Persist everything to Supabase
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, date
from typing import Any

import feedparser

# ---------------------------------------------------------------------------
# RSS feed sources
# ---------------------------------------------------------------------------
RSS_FEEDS: list[dict[str, str]] = [
    {
        "url": "https://www.moneycontrol.com/rss/latestnews.xml",
        "source": "moneycontrol",
    },
    {
        "url": "https://www.moneycontrol.com/rss/marketreports.xml",
        "source": "moneycontrol",
    },
    {
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source": "economic_times",
    },
    {
        "url": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
        "source": "economic_times",
    },
]

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


def fetch_news() -> list[dict[str, Any]]:
    """
    Fetch articles from all configured RSS feeds.

    Returns:
        list of dicts with keys: url, title, source, published_at, fetched_at
    """
    now = datetime.now(timezone.utc).isoformat()
    seen_urls: set[str] = set()
    articles: list[dict[str, Any]] = []

    for feed_cfg in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
        except Exception as exc:
            print(f"Warning: failed to parse {feed_cfg['url']}: {exc}")
            continue

        for entry in feed.entries:
            url = getattr(entry, "link", None)
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(
                        *entry.published_parsed[:6], tzinfo=timezone.utc
                    ).isoformat()
                except Exception:
                    pass
            if published_at is None:
                published_at = now

            articles.append(
                {
                    "url": url,
                    "title": getattr(entry, "title", ""),
                    "source": feed_cfg["source"],
                    "published_at": published_at,
                    "fetched_at": now,
                }
            )

    print(f"Fetched {len(articles)} unique articles from {len(RSS_FEEDS)} RSS feeds.")
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

        relevance = 1.0 if len(symbols) == 1 else round(1.0 / len(symbols), 4)
        for sym in symbols:
            sentiments.append(
                {
                    "article_id": article["id"],
                    "symbol": sym,
                    "positive_prob": pos,
                    "negative_prob": neg,
                    "neutral_prob": neu,
                    "sentiment_label": label,
                    "relevance_score": relevance,
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
        pos_avg = round(sum(r["positive_prob"] for r in rows) / n, 6)
        neg_avg = round(sum(r["negative_prob"] for r in rows) / n, 6)
        neu_avg = round(sum(r["neutral_prob"] for r in rows) / n, 6)
        avg_sentiment = round(pos_avg - neg_avg, 6)
        daily.append(
            {
                "symbol": symbol,
                "date": day,
                "avg_sentiment": avg_sentiment,
                "positive_avg": pos_avg,
                "negative_avg": neg_avg,
                "neutral_avg": neu_avg,
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

    from services.ml.ingest.store import (
        upsert_news_articles,
        upsert_article_sentiments,
        upsert_daily_sentiment,
    )

    start = time.time()

    # --- fetch ---
    print("=" * 60)
    print("SENTIMENT STEP 1: Fetching news from RSS feeds")
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
    from services.ml.config import get_supabase

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
