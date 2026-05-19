"""
Email notification service — local console stub.

Replaces the Resend API integration with a simple console logger
so callers keep working without an external email provider.
"""

from __future__ import annotations

from datetime import datetime, timezone


def send_signal_change_email(
    to_email: str,
    symbol: str,
    old_signal: str,
    new_signal: str,
    confidence: float,
) -> bool:
    """
    Log a signal-change notification to the console instead of sending
    an email.  Always returns True so callers treat it as "sent".
    """
    old_label = _format_signal(old_signal)
    new_label = _format_signal(new_signal)
    confidence_pct = f"{confidence * 100:.0f}%"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print(
        f"  [email][{now}] To: {to_email} | "
        f"Subject: Signal Change: {symbol} — {old_label} -> {new_label} | "
        f"Confidence: {confidence_pct}"
    )
    return True


def _format_signal(signal: str) -> str:
    return signal.replace("_", " ").title()


def _signal_color(signal: str) -> str:
    colors = {
        "strong_buy": "#22c55e",
        "buy": "#10b981",
        "hold": "#eab308",
        "sell": "#f97316",
        "strong_sell": "#ef4444",
    }
    return colors.get(signal, "#94a3b8")
