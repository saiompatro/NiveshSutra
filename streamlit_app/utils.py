"""Shared utilities: formatting, signal colors, personalization logic."""


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_currency(value: float) -> str:
    """Format a number as INR currency string."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "₹0"
    if abs(v) >= 1_00_00_000:  # 1 crore
        return f"₹{v / 1_00_00_000:.2f} Cr"
    if abs(v) >= 1_00_000:     # 1 lakh
        return f"₹{v / 1_00_000:.2f} L"
    return f"₹{v:,.0f}"


def format_pct(value: float, decimals: int = 2) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_signal(signal: str) -> str:
    return signal.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Signal colors (as hex strings for Plotly / st.markdown HTML)
# ---------------------------------------------------------------------------

SIGNAL_COLORS = {
    "strong_buy":  "#22c55e",
    "buy":         "#10b981",
    "hold":        "#eab308",
    "sell":        "#f97316",
    "strong_sell": "#ef4444",
}

SIGNAL_BG = {
    "strong_buy":  "#14532d",
    "buy":         "#064e3b",
    "hold":        "#713f12",
    "sell":        "#7c2d12",
    "strong_sell": "#7f1d1d",
}


def signal_color(signal: str) -> str:
    return SIGNAL_COLORS.get(signal, "#94a3b8")


def signal_badge_html(signal: str) -> str:
    color = SIGNAL_COLORS.get(signal, "#94a3b8")
    bg = SIGNAL_BG.get(signal, "#1e293b")
    label = format_signal(signal)
    return (
        f'<span style="background:{bg};color:{color};padding:2px 8px;'
        f'border-radius:4px;font-size:0.78rem;font-weight:600;">{label}</span>'
    )


# ---------------------------------------------------------------------------
# Signals personalization (ported from signals/page.tsx)
# ---------------------------------------------------------------------------

def get_confidence_threshold(risk_profile: str) -> float:
    return {"conservative": 0.5, "aggressive": 0.2}.get(risk_profile, 0.3)


def _conservative_score(s: dict) -> float:
    weights = {"buy": 3, "hold": 2, "strong_buy": 1, "sell": 0, "strong_sell": -1}
    return weights.get(s.get("signal", ""), 0) + s.get("confidence", 0) * 2


def _aggressive_score(s: dict) -> float:
    weights = {"strong_buy": 4, "strong_sell": 3, "buy": 2, "sell": 1, "hold": 0}
    return weights.get(s.get("signal", ""), 0) + s.get("confidence", 0) * 2


def personalize_signals(signals: list[dict], risk_profile: str) -> list[dict]:
    if risk_profile == "conservative":
        return sorted(signals, key=_conservative_score, reverse=True)
    if risk_profile == "aggressive":
        return sorted(signals, key=_aggressive_score, reverse=True)
    return signals


def get_position_size_hint(risk_profile: str, signal: str) -> str:
    hints = {
        "conservative": {"buy": "2–3% of portfolio", "strong_buy": "3–5% of portfolio"},
        "moderate":     {"buy": "3–5% of portfolio", "strong_buy": "5–8% of portfolio"},
        "aggressive":   {"buy": "5–8% of portfolio", "strong_buy": "8–12% of portfolio"},
    }
    return hints.get(risk_profile, {}).get(signal, "")


# ---------------------------------------------------------------------------
# Risk assessment scoring (from profile/route.ts)
# ---------------------------------------------------------------------------

def compute_risk_profile(answers: list[int]) -> tuple[int, str]:
    """Given a list of answer scores, return (total_score, risk_profile)."""
    total = sum(answers)
    if total <= 8:
        return total, "conservative"
    elif total <= 12:
        return total, "moderate"
    else:
        return total, "aggressive"
