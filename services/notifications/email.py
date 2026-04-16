"""
Email notification service using Resend API.

Sends signal change alerts to users who have accepted signals
and enabled email notifications.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone


RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "NiveshSutra <noreply@niveshsutra.com>")


def send_signal_change_email(
    to_email: str,
    symbol: str,
    old_signal: str,
    new_signal: str,
    confidence: float,
) -> bool:
    """
    Send an email notifying the user that a tracked signal has changed.

    Returns True if the email was sent successfully.
    """
    if not RESEND_API_KEY:
        print(f"  [email] RESEND_API_KEY not set — skipping email to {to_email} for {symbol}")
        return False

    try:
        import resend

        resend.api_key = RESEND_API_KEY

        old_label = _format_signal(old_signal)
        new_label = _format_signal(new_signal)
        confidence_pct = f"{confidence * 100:.0f}%"

        subject = f"Signal Change: {symbol} — {old_label} → {new_label}"

        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1a1a2e; color: #fff; padding: 24px; border-radius: 12px;">
                <h2 style="margin: 0 0 8px; color: #e2e8f0;">Signal Changed for {symbol}</h2>
                <p style="color: #94a3b8; margin: 0 0 24px;">Your tracked stock has a new signal.</p>

                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
                    <div style="background: #2d2d44; padding: 16px 24px; border-radius: 8px; text-align: center;">
                        <p style="color: #94a3b8; font-size: 12px; margin: 0 0 4px;">Previous</p>
                        <p style="font-size: 18px; font-weight: 700; margin: 0; color: {_signal_color(old_signal)};">{old_label}</p>
                    </div>
                    <span style="font-size: 24px; color: #64748b;">→</span>
                    <div style="background: #2d2d44; padding: 16px 24px; border-radius: 8px; text-align: center;">
                        <p style="color: #94a3b8; font-size: 12px; margin: 0 0 4px;">New Signal</p>
                        <p style="font-size: 18px; font-weight: 700; margin: 0; color: {_signal_color(new_signal)};">{new_label}</p>
                    </div>
                </div>

                <p style="color: #94a3b8; font-size: 14px; margin: 0 0 16px;">
                    Confidence: <strong style="color: #e2e8f0;">{confidence_pct}</strong>
                </p>

                <p style="color: #64748b; font-size: 12px; margin: 16px 0 0;">
                    This is an automated alert from NiveshSutra. You can manage your tracked signals
                    and notification preferences in Settings.
                </p>
            </div>
        </div>
        """

        resend.Emails.send(
            {
                "from": RESEND_FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        )

        print(f"  [email] Sent signal change email to {to_email} for {symbol}: {old_label} → {new_label}")
        return True

    except Exception as e:
        print(f"  [email] Failed to send email to {to_email} for {symbol}: {e}")
        return False


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
