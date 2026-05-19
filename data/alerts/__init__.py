"""
Alert generator for NiveshSutra.

Checks for three types of alerts:
  1. Signal changes  (e.g., "TCS signal changed from hold to buy")
  2. Sentiment shifts (e.g., "INFY sentiment turned bearish")
  3. Rebalance drift  (e.g., "Portfolio drift exceeds 10% threshold")
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from backend.database import SessionLocal, DEFAULT_USER_ID
from backend.models.db_models import (
    Signal, SentimentDaily, PortfolioOptimization,
    OptimizationAllocation, Holding, Alert,
)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
SENTIMENT_SHIFT_THRESHOLD = 0.3  # absolute change in avg_sentiment
DRIFT_THRESHOLD = 0.10  # 10% portfolio drift


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_alerts() -> list[dict]:
    """
    Check for alert conditions and insert new alerts into the database.

    Returns:
        List of alert dicts that were inserted.
    """
    start = time.time()
    session = SessionLocal()
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    all_alerts: list[dict] = []

    try:
        print("=" * 60)
        print("ALERTS STEP 1: Checking signal changes")
        print("=" * 60)
        signal_alerts = _check_signal_changes(session, today_str, yesterday_str)
        all_alerts.extend(signal_alerts)
        print(f"  Found {len(signal_alerts)} signal change alerts.")

        print()
        print("=" * 60)
        print("ALERTS STEP 2: Checking sentiment shifts")
        print("=" * 60)
        sentiment_alerts = _check_sentiment_shifts(session, today_str, yesterday_str)
        all_alerts.extend(sentiment_alerts)
        print(f"  Found {len(sentiment_alerts)} sentiment shift alerts.")

        print()
        print("=" * 60)
        print("ALERTS STEP 3: Checking portfolio drift")
        print("=" * 60)
        drift_alerts = _check_rebalance_drift(session)
        all_alerts.extend(drift_alerts)
        print(f"  Found {len(drift_alerts)} drift alerts.")

        if all_alerts:
            print()
            print(f"Inserting {len(all_alerts)} alerts into database...")
            for alert_dict in all_alerts:
                alert_obj = Alert(
                    user_id=alert_dict.get("user_id", DEFAULT_USER_ID),
                    alert_type=alert_dict["alert_type"],
                    title=alert_dict["title"],
                    message=alert_dict.get("message"),
                    symbol=alert_dict.get("symbol"),
                    is_read=alert_dict.get("is_read", False),
                )
                session.add(alert_obj)
            session.commit()
            print(f"Inserted {len(all_alerts)} alerts.")
        else:
            print("\nNo alerts to generate.")

    finally:
        session.close()

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"ALERTS DONE in {elapsed:.1f}s -- {len(all_alerts)} alerts generated.")
    print("=" * 60)

    return all_alerts


def _check_signal_changes(session: Any, today_str: str, yesterday_str: str) -> list[dict]:
    alerts: list[dict] = []

    today_rows = (
        session.query(Signal.symbol, Signal.signal)
        .filter(Signal.date == today_str)
        .all()
    )
    yesterday_rows = (
        session.query(Signal.symbol, Signal.signal)
        .filter(Signal.date == yesterday_str)
        .all()
    )

    today_map = {r.symbol: r.signal for r in today_rows}
    yesterday_map = {r.symbol: r.signal for r in yesterday_rows}

    for symbol, new_signal in today_map.items():
        old_signal = yesterday_map.get(symbol)
        if old_signal and old_signal != new_signal:
            alerts.append(
                {
                    "alert_type": "signal_change",
                    "title": f"{symbol} signal changed",
                    "message": f"{symbol} signal changed from {old_signal} to {new_signal}.",
                    "symbol": symbol,
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return alerts


def _check_sentiment_shifts(session: Any, today_str: str, yesterday_str: str) -> list[dict]:
    """Flag symbols whose daily sentiment shifted significantly."""
    alerts: list[dict] = []

    today_rows = (
        session.query(SentimentDaily.symbol, SentimentDaily.avg_sentiment)
        .filter(SentimentDaily.date == today_str)
        .all()
    )
    yesterday_rows = (
        session.query(SentimentDaily.symbol, SentimentDaily.avg_sentiment)
        .filter(SentimentDaily.date == yesterday_str)
        .all()
    )

    today_map = {r.symbol: r.avg_sentiment for r in today_rows}
    yesterday_map = {r.symbol: r.avg_sentiment for r in yesterday_rows}

    for symbol, new_sent in today_map.items():
        old_sent = yesterday_map.get(symbol)
        if old_sent is None:
            continue
        delta = new_sent - old_sent
        if abs(delta) >= SENTIMENT_SHIFT_THRESHOLD:
            direction = "bullish" if delta > 0 else "bearish"
            alerts.append(
                {
                    "alert_type": "sentiment_shift",
                    "title": f"{symbol} sentiment turned {direction}",
                    "message": (
                        f"{symbol} daily sentiment shifted by {delta:+.2f} "
                        f"(from {old_sent:.2f} to {new_sent:.2f}), turning {direction}."
                    ),
                    "symbol": symbol,
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return alerts


def _check_rebalance_drift(session: Any) -> list[dict]:
    """
    For each user with a completed optimization, check if current portfolio
    has drifted more than DRIFT_THRESHOLD from recommended weights.
    """
    alerts: list[dict] = []

    opt_rows = (
        session.query(PortfolioOptimization.id, PortfolioOptimization.user_id)
        .filter(PortfolioOptimization.status == "completed")
        .order_by(PortfolioOptimization.created_at.desc())
        .limit(100)
        .all()
    )
    if not opt_rows:
        return alerts

    seen_users: set[str] = set()
    latest_opts: list[dict] = []
    for row in opt_rows:
        if row.user_id not in seen_users:
            seen_users.add(row.user_id)
            latest_opts.append({"id": row.id, "user_id": row.user_id})

    for opt in latest_opts:
        opt_id = opt["id"]
        user_id = opt["user_id"]

        alloc_rows = (
            session.query(
                OptimizationAllocation.symbol,
                OptimizationAllocation.recommended_weight,
            )
            .filter(OptimizationAllocation.optimization_id == opt_id)
            .all()
        )
        if not alloc_rows:
            continue

        rec_weights = {r.symbol: r.recommended_weight for r in alloc_rows}

        holdings_rows = (
            session.query(Holding.symbol, Holding.quantity, Holding.avg_buy_price)
            .filter(Holding.user_id == user_id)
            .all()
        )
        if not holdings_rows:
            continue

        total_value = 0.0
        current_values: dict[str, float] = {}
        for h in holdings_rows:
            val = (h.quantity or 0) * (h.avg_buy_price or 0)
            current_values[h.symbol] = val
            total_value += val

        if total_value <= 0:
            continue

        current_weights = {s: v / total_value for s, v in current_values.items()}

        max_drift = 0.0
        drift_symbol = None
        all_symbols = set(rec_weights.keys()) | set(current_weights.keys())
        for sym in all_symbols:
            rec_w = rec_weights.get(sym, 0.0)
            cur_w = current_weights.get(sym, 0.0)
            drift = abs(cur_w - rec_w)
            if drift > max_drift:
                max_drift = drift
                drift_symbol = sym

        if max_drift >= DRIFT_THRESHOLD:
            alerts.append(
                {
                    "user_id": user_id,
                    "alert_type": "rebalance_drift",
                    "title": "Portfolio drift exceeds threshold",
                    "message": (
                        f"Your portfolio has drifted from recommended allocations. "
                        f"Maximum drift: {max_drift:.1%} on {drift_symbol}. "
                        f"Consider rebalancing."
                    ),
                    "symbol": drift_symbol,
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    return alerts
