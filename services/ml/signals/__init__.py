"""
Hybrid signal computation engine.

composite_score = 0.4 * technical + 0.3 * sentiment + 0.3 * momentum

Signal mapping:
    >= 0.5  -> strong_buy
    >= 0.2  -> buy
    >= -0.2 -> hold
    >= -0.5 -> sell
    <  -0.5 -> strong_sell

confidence = min(|composite| * 2, 1.0)
"""

from __future__ import annotations

import time
from collections import Counter
from datetime import date
from typing import Any

import numpy as np

from services.ml.config import get_supabase

# ---------------------------------------------------------------------------
# Normalizers  (each returns a float in [-1, +1])
# ---------------------------------------------------------------------------


def normalize_rsi(rsi_value: float | None) -> float:
    """
    Normalize RSI into [-1, +1].
    30 (oversold) -> +1, 50 -> 0, 70 (overbought) -> -1.
    """
    if rsi_value is None:
        return 0.0
    clamped = max(0.0, min(100.0, rsi_value))
    # Linear: score = (50 - rsi) / 20, clamped to [-1, 1]
    score = (50.0 - clamped) / 20.0
    return max(-1.0, min(1.0, score))


def normalize_macd(macd_hist: float | None) -> float:
    """
    Normalize MACD histogram into [-1, +1].
    Positive histogram -> bullish (+), negative -> bearish (-).
    Uses tanh for smooth saturation.
    """
    if macd_hist is None:
        return 0.0
    return float(np.tanh(macd_hist / 5.0))


def normalize_bb(
    close: float | None, bb_upper: float | None, bb_lower: float | None
) -> float:
    """
    Normalize Bollinger Band position into [-1, +1].
    Close near lower band -> +1 (oversold / buy signal).
    Close near upper band -> -1 (overbought / sell signal).
    """
    if close is None or bb_upper is None or bb_lower is None:
        return 0.0
    band_width = bb_upper - bb_lower
    if band_width <= 0:
        return 0.0
    position = (close - bb_lower) / band_width  # 0..1
    score = 1.0 - 2.0 * position  # +1 at lower, -1 at upper
    return max(-1.0, min(1.0, score))


def normalize_obv(obv_series: list[float] | None) -> float:
    """
    Normalize OBV trend into [-1, +1].
    Computes slope of last 20 OBV values via linear regression, then tanh.
    """
    if obv_series is None or len(obv_series) < 5:
        return 0.0
    arr = np.array(obv_series[-20:], dtype=float)
    x = np.arange(len(arr), dtype=float)
    # Simple slope via least-squares
    n = len(arr)
    slope = (n * np.dot(x, arr) - x.sum() * arr.sum()) / (
        n * np.dot(x, x) - x.sum() ** 2 + 1e-12
    )
    # Normalize relative to mean OBV magnitude
    mean_obv = np.abs(arr).mean() + 1e-12
    normalized = slope / mean_obv
    return float(np.tanh(normalized * 50.0))


# ---------------------------------------------------------------------------
# Composite scores
# ---------------------------------------------------------------------------


def compute_technical_score(indicators_row: dict[str, Any]) -> float:
    """
    technical_score = 0.3*RSI + 0.3*MACD + 0.2*BB + 0.2*OBV
    """
    rsi = normalize_rsi(indicators_row.get("rsi_14"))
    macd = normalize_macd(indicators_row.get("macd_hist"))
    bb = normalize_bb(
        indicators_row.get("close"),
        indicators_row.get("bb_upper"),
        indicators_row.get("bb_lower"),
    )
    obv = normalize_obv(indicators_row.get("obv_series"))
    return round(0.3 * rsi + 0.3 * macd + 0.2 * bb + 0.2 * obv, 6)


def compute_momentum_score(ohlcv_rows: list[dict]) -> float:
    """
    momentum_score = mean(5d_return, 20d_return, SMA_crossover)
    Each normalized to [-1, +1].
    ohlcv_rows should be sorted oldest-first with at least 20 rows.
    """
    if not ohlcv_rows or len(ohlcv_rows) < 2:
        return 0.0

    closes = [r["close"] for r in ohlcv_rows if r.get("close") is not None]
    if len(closes) < 2:
        return 0.0

    current = closes[-1]

    # 5-day return
    ret_5d = 0.0
    if len(closes) >= 6:
        prev_5 = closes[-6]
        if prev_5 and prev_5 != 0:
            ret_5d = float(np.tanh(((current - prev_5) / prev_5) * 10.0))

    # 20-day return
    ret_20d = 0.0
    if len(closes) >= 21:
        prev_20 = closes[-21]
        if prev_20 and prev_20 != 0:
            ret_20d = float(np.tanh(((current - prev_20) / prev_20) * 5.0))

    # SMA crossover: SMA_10 vs SMA_50
    sma_cross = 0.0
    if len(closes) >= 50:
        sma_10 = np.mean(closes[-10:])
        sma_50 = np.mean(closes[-50:])
        if sma_50 != 0:
            diff = (sma_10 - sma_50) / sma_50
            sma_cross = float(np.tanh(diff * 20.0))

    return round((ret_5d + ret_20d + sma_cross) / 3.0, 6)


def compute_composite(
    tech: float, sent: float, momentum: float
) -> tuple[float, str, float]:
    """
    composite = 0.4*tech + 0.3*sent + 0.3*momentum

    Returns (composite_score, signal_label, confidence).
    """
    composite = round(0.4 * tech + 0.3 * sent + 0.3 * momentum, 6)

    if composite >= 0.5:
        signal = "strong_buy"
    elif composite >= 0.2:
        signal = "buy"
    elif composite >= -0.2:
        signal = "hold"
    elif composite >= -0.5:
        signal = "sell"
    else:
        signal = "strong_sell"

    confidence = round(min(abs(composite) * 2.0, 1.0), 4)
    return composite, signal, confidence


# ---------------------------------------------------------------------------
# Explanation generator
# ---------------------------------------------------------------------------


def generate_explanation(
    tech: float, sent: float, momentum: float, signal: str
) -> str:
    """Generate a template-based human-readable explanation."""

    def _describe(val: float, name: str) -> str:
        if val >= 0.3:
            return f"{name} is strongly bullish"
        elif val >= 0.1:
            return f"{name} is mildly bullish"
        elif val > -0.1:
            return f"{name} is neutral"
        elif val > -0.3:
            return f"{name} is mildly bearish"
        else:
            return f"{name} is strongly bearish"

    parts = [
        _describe(tech, "Technical analysis"),
        _describe(sent, "Market sentiment"),
        _describe(momentum, "Price momentum"),
    ]

    signal_map = {
        "strong_buy": "Strong Buy",
        "buy": "Buy",
        "hold": "Hold",
        "sell": "Sell",
        "strong_sell": "Strong Sell",
    }

    return f"{'; '.join(parts)}. Overall signal: {signal_map.get(signal, signal)}."


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def run_signals_pipeline() -> None:
    """
    Read indicators + sentiment from Supabase, compute signals for all stocks,
    and store via upsert_signals.
    """
    from services.ml.ingest.store import upsert_signals

    start = time.time()
    sb = get_supabase()
    today_str = date.today().isoformat()

    # --- 1. Get active signal config weights (or use defaults) ---
    print("=" * 60)
    print("SIGNALS STEP 1: Loading configuration")
    print("=" * 60)
    tech_w, sent_w, mom_w = 0.4, 0.3, 0.3
    try:
        cfg_resp = (
            sb.table("signal_config")
            .select("technical_weight,sentiment_weight,momentum_weight")
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if cfg_resp.data:
            row = cfg_resp.data[0]
            tech_w = row.get("technical_weight", tech_w)
            sent_w = row.get("sentiment_weight", sent_w)
            mom_w = row.get("momentum_weight", mom_w)
            print(
                f"  Using config weights: tech={tech_w}, sent={sent_w}, mom={mom_w}"
            )
        else:
            print(
                f"  No active config found; using defaults: "
                f"tech={tech_w}, sent={sent_w}, mom={mom_w}"
            )
    except Exception:
        print(
            f"  Config table not available; using defaults: "
            f"tech={tech_w}, sent={sent_w}, mom={mom_w}"
        )

    # --- 2. Get list of stocks ---
    print()
    print("=" * 60)
    print("SIGNALS STEP 2: Loading stock list")
    print("=" * 60)
    stocks_resp = sb.table("stocks").select("symbol").execute()
    symbols = [row["symbol"] for row in stocks_resp.data]
    print(f"  Found {len(symbols)} stocks.")

    if not symbols:
        print("No stocks found in DB. Exiting.")
        return

    # --- 3. Load latest indicators for each stock ---
    print()
    print("=" * 60)
    print("SIGNALS STEP 3: Computing signals for each stock")
    print("=" * 60)

    signal_rows: list[dict] = []

    for sym in symbols:
        # Latest indicator row
        ind_resp = (
            sb.table("technical_indicators")
            .select("*")
            .eq("symbol", sym)
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        indicators = ind_resp.data[0] if ind_resp.data else {}

        # Recent OHLCV for momentum (last 60 days)
        ohlcv_resp = (
            sb.table("ohlcv")
            .select("date,close")
            .eq("symbol", sym)
            .order("date", desc=True)
            .limit(60)
            .execute()
        )
        ohlcv_rows = (
            sorted(ohlcv_resp.data, key=lambda r: r["date"])
            if ohlcv_resp.data
            else []
        )

        # OBV series for the indicator normalizer
        obv_resp = (
            sb.table("technical_indicators")
            .select("obv")
            .eq("symbol", sym)
            .order("date", desc=True)
            .limit(20)
            .execute()
        )
        obv_series = (
            [r["obv"] for r in reversed(obv_resp.data) if r.get("obv") is not None]
            if obv_resp.data
            else []
        )
        indicators["obv_series"] = obv_series

        # Also add close from OHLCV for BB normalization
        if ohlcv_rows:
            indicators.setdefault("close", ohlcv_rows[-1].get("close"))

        # Daily sentiment
        sent_resp = (
            sb.table("sentiment_daily")
            .select("avg_sentiment")
            .eq("symbol", sym)
            .eq("date", today_str)
            .limit(1)
            .execute()
        )
        sentiment_score = (
            sent_resp.data[0]["avg_sentiment"] if sent_resp.data else 0.0
        )

        # Compute scores
        tech_score = compute_technical_score(indicators)
        mom_score = compute_momentum_score(ohlcv_rows)

        # Use configurable weights for composite
        raw_composite = (
            tech_w * tech_score + sent_w * sentiment_score + mom_w * mom_score
        )
        composite = round(raw_composite, 6)

        if composite >= 0.5:
            signal = "strong_buy"
        elif composite >= 0.2:
            signal = "buy"
        elif composite >= -0.2:
            signal = "hold"
        elif composite >= -0.5:
            signal = "sell"
        else:
            signal = "strong_sell"

        confidence = round(min(abs(composite) * 2.0, 1.0), 4)
        explanation = generate_explanation(
            tech_score, sentiment_score, mom_score, signal
        )

        signal_rows.append(
            {
                "symbol": sym,
                "date": today_str,
                "technical_score": tech_score,
                "sentiment_score": round(sentiment_score, 6),
                "momentum_score": mom_score,
                "composite_score": composite,
                "signal": signal,
                "confidence": confidence,
                "explanation": explanation,
            }
        )

    # --- 4. Store ---
    print()
    print("=" * 60)
    print("SIGNALS STEP 4: Storing signals")
    print("=" * 60)
    upsert_signals(signal_rows)

    # --- 5. Signal Change Notifications ---
    print()
    print("=" * 60)
    print("SIGNALS STEP 5: Checking for signal change notifications")
    print("=" * 60)
    _check_signal_change_notifications(sb, signal_rows)

    elapsed = time.time() - start
    print()
    print("=" * 60)
    print(f"SIGNALS PIPELINE DONE in {elapsed:.1f}s")
    print(f"  Signals computed: {len(signal_rows)}")

    # Quick summary
    counts = Counter(r["signal"] for r in signal_rows)
    for sig_label in ["strong_buy", "buy", "hold", "sell", "strong_sell"]:
        print(f"    {sig_label}: {counts.get(sig_label, 0)}")
    print("=" * 60)


def _check_signal_change_notifications(sb: Any, signal_rows: list[dict]) -> None:
    """
    Check all active signal notifications. If a tracked signal has changed,
    send an email (respecting 24h cooldown) and update the tracking record.
    """
    from datetime import datetime, timezone, timedelta

    try:
        # Get all active notification subscriptions
        notif_resp = (
            sb.table("signal_notifications")
            .select("id, user_id, symbol, last_signal, last_notified_at")
            .eq("is_active", True)
            .execute()
        )
        if not notif_resp.data:
            print("  No active signal notifications to check.")
            return

        # Build a lookup of new signals by symbol
        signal_map = {r["symbol"]: r for r in signal_rows}

        # Get user emails + notification preferences in bulk
        user_ids = list({n["user_id"] for n in notif_resp.data})
        profiles_resp = (
            sb.table("profiles")
            .select("id, email_notifications_enabled")
            .in_("id", user_ids)
            .execute()
        )
        profile_map = {p["id"]: p for p in (profiles_resp.data or [])}

        # Supabase auth admin: get user emails
        # We need the service role client for auth.admin
        email_map: dict[str, str] = {}
        for uid in user_ids:
            try:
                user_resp = sb.auth.admin.get_user_by_id(uid)
                if user_resp and user_resp.user:
                    email_map[uid] = user_resp.user.email or ""
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        cooldown = timedelta(hours=24)
        emails_sent = 0
        signals_changed = 0

        for notif in notif_resp.data:
            symbol = notif["symbol"]
            new_signal_data = signal_map.get(symbol)
            if not new_signal_data:
                continue

            new_signal = new_signal_data["signal"]
            old_signal = notif.get("last_signal")

            # Always update the last_signal field
            if old_signal != new_signal:
                signals_changed += 1
                update_data: dict[str, Any] = {"last_signal": new_signal}

                # Check if we should send an email
                user_profile = profile_map.get(notif["user_id"], {})
                email_enabled = user_profile.get("email_notifications_enabled", False)
                user_email = email_map.get(notif["user_id"], "")

                should_send = email_enabled and user_email and old_signal is not None

                # Respect 24h cooldown
                if should_send and notif.get("last_notified_at"):
                    last_notified = datetime.fromisoformat(
                        notif["last_notified_at"].replace("Z", "+00:00")
                    )
                    if now - last_notified < cooldown:
                        should_send = False
                        print(f"  {symbol} ({notif['user_id'][:8]}...): signal changed but cooldown active")

                if should_send:
                    try:
                        from services.notifications.email import send_signal_change_email

                        sent = send_signal_change_email(
                            to_email=user_email,
                            symbol=symbol,
                            old_signal=old_signal,
                            new_signal=new_signal,
                            confidence=new_signal_data.get("confidence", 0),
                        )
                        if sent:
                            update_data["last_notified_at"] = now.isoformat()
                            emails_sent += 1
                    except Exception as e:
                        print(f"  [notify] Email error for {symbol}: {e}")

                # Update the notification record
                sb.table("signal_notifications").update(update_data).eq(
                    "id", notif["id"]
                ).execute()

        print(f"  Checked {len(notif_resp.data)} tracked signals.")
        print(f"  Signals changed: {signals_changed}")
        print(f"  Emails sent: {emails_sent}")

    except Exception as e:
        print(f"  [notify] Signal notification check failed: {e}")
