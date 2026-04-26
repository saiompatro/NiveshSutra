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

from data.config import get_supabase

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
    Check for alert conditions and insert new alerts into Supabase.

    Returns:
        List of alert dicts that were inserted.
    """
    start = time.time()
    sb = get_supabase()
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    all_alerts: list[dict] = []

    print("=" * 60)
    print("ALERTS STEP 1: Checking signal changes")
    print("=" * 60)
    signal_alerts = _check_signal_changes(sb, today_str, yesterday_str)
    all_alerts.extend(signal_alerts)
    print(f"  Found {len(signal_alerts)} signal change alerts.")

    print()
    print("=" * 60)
    print("ALERTS STEP 2: Checking sentiment shifts")
    print("=" * 60)
    sentiment_alerts = _check_sentiment_shifts(sb, today_str, yesterday_str)
    all_alerts.extend(sentiment_alerts)
    print(f"  Found {len(sentiment_alerts)} sentiment shift alerts.")

    print()
    print("=" * 60)
    print("ALERTS STEP 3: Checking portfolio drift")
    print("=" * 60)
    drift_alerts = _check_rebalance_drift(sb)
    all_alerts.extend(drift_alerts)
    print(f"  Found {len(drift_alerts)} drift alerts.")

    if all_alerts:
        print()
        print(f"Inserting {len(all_alerts)} alerts into Supabase...")
        batch_size = 100
        for i in range(0, len(all_alerts), batch_size):
            batch = all_alerts[i : i + batch_size]
            sb.table("alerts").insert(batch).execute()
        print(f"Inserted {len(all_alerts)} alerts.")
    else:
        print("\nNo alerts to generate.")

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"ALERTS DONE in {elapsed:.1f}s -- {len(all_alerts)} alerts generated.")
    print("=" * 60)

    return all_alerts


def _check_signal_changes(sb: Any, today_str: str, yesterday_str: str) -> list[dict]:
    alerts: list[dict] = []

    today_resp = (
        sb.table("signals").select("symbol,signal").eq("date", today_str).execute()
    )
    yesterday_resp = (
        sb.table("signals").select("symbol,signal").eq("date", yesterday_str).execute()
    )

    today_map = {r["symbol"]: r["signal"] for r in today_resp.data} if today_resp.data else {}
    yesterday_map = {r["symbol"]: r["signal"] for r in yesterday_resp.data} if yesterday_resp.data else {}

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


def _check_sentiment_shifts(sb: Any, today_str: str, yesterday_str: str) -> list[dict]:
    """Flag symbols whose daily sentiment shifted significantly."""
    alerts: list[dict] = []

    today_resp = (
        sb.table("sentiment_daily").select("symbol,avg_sentiment").eq("date", today_str).execute()
    )
    yesterday_resp = (
        sb.table("sentiment_daily").select("symbol,avg_sentiment").eq("date", yesterday_str).execute()
    )

    today_map = {r["symbol"]: r["avg_sentiment"] for r in today_resp.data} if today_resp.data else {}
    yesterday_map = {r["symbol"]: r["avg_sentiment"] for r in yesterday_resp.data} if yesterday_resp.data else {}

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


def _check_rebalance_drift(sb: Any) -> list[dict]:
    """
    For each user with a completed optimization, check if current portfolio
    has drifted more than DRIFT_THRESHOLD from recommended weights.
    """
    alerts: list[dict] = []

    opt_resp = (
        sb.table("portfolio_optimizations")
        .select("id,user_id")
        .eq("status", "completed")
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    if not opt_resp.data:
        return alerts

    seen_users: set[str] = set()
    latest_opts: list[dict] = []
    for row in opt_resp.data:
        if row["user_id"] not in seen_users:
            seen_users.add(row["user_id"])
            latest_opts.append(row)

    for opt in latest_opts:
        opt_id = opt["id"]
        user_id = opt["user_id"]

        alloc_resp = (
            sb.table("optimization_allocations")
            .select("symbol,recommended_weight")
            .eq("optimization_id", opt_id)
            .execute()
        )
        if not alloc_resp.data:
            continue

        rec_weights = {r["symbol"]: r["recommended_weight"] for r in alloc_resp.data}

        holdings_resp = (
            sb.table("holdings")
            .select("symbol,quantity,avg_buy_price")
            .eq("user_id", user_id)
            .execute()
        )
        if not holdings_resp.data:
            continue

        total_value = 0.0
        current_values: dict[str, float] = {}
        for h in holdings_resp.data:
            val = (h.get("quantity", 0) or 0) * (h.get("avg_buy_price", 0) or 0)
            current_values[h["symbol"]] = val
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
