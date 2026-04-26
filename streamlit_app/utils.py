"""Shared utilities: formatting, signal colors, and personalization logic."""


RISK_QUESTIONS = [
    {
        "q": "1. What is your primary investment goal?",
        "options": [
            ("Preserve capital with minimal risk", 1),
            ("Steady income with moderate growth", 2),
            ("Long-term capital growth", 3),
        ],
    },
    {
        "q": "2. How long is your investment horizon?",
        "options": [
            ("Less than 2 years", 1),
            ("2-5 years", 2),
            ("More than 5 years", 3),
        ],
    },
    {
        "q": "3. How would you react to a 20% portfolio drop?",
        "options": [
            ("Sell immediately to cut losses", 1),
            ("Wait and see if it recovers", 2),
            ("Buy more at the lower price", 3),
        ],
    },
    {
        "q": "4. What percentage of your savings is this investment?",
        "options": [
            ("More than 75%", 1),
            ("25-75%", 2),
            ("Less than 25%", 3),
        ],
    },
    {
        "q": "5. How familiar are you with equity markets?",
        "options": [
            ("Not familiar", 1),
            ("Some knowledge", 2),
            ("Experienced investor", 3),
        ],
    },
]


def format_currency(value: float) -> str:
    """Format a number as an INR currency string using ASCII-safe text."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "Rs 0"
    if abs(numeric_value) >= 1_00_00_000:
        return f"Rs {numeric_value / 1_00_00_000:.2f} Cr"
    if abs(numeric_value) >= 1_00_000:
        return f"Rs {numeric_value / 1_00_000:.2f} L"
    return f"Rs {numeric_value:,.0f}"


def format_pct(value: float, decimals: int = 2) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_signal(signal: str) -> str:
    return signal.replace("_", " ").title()


SIGNAL_COLORS = {
    "strong_buy": "#23C55E",
    "buy": "#2F80ED",
    "hold": "#8B949E",
    "sell": "#EF4444",
    "strong_sell": "#EF4444",
}

SIGNAL_BG = {
    "strong_buy": "rgba(35, 197, 94, 0.14)",
    "buy":        "rgba(47, 128, 237, 0.14)",
    "hold":       "rgba(139, 148, 158, 0.14)",
    "sell":       "rgba(239, 68, 68, 0.14)",
    "strong_sell":"rgba(239, 68, 68, 0.14)",
}


def signal_color(signal: str) -> str:
    return SIGNAL_COLORS.get(signal, "#8B949E")


def signal_badge_html(signal: str) -> str:
    color = SIGNAL_COLORS.get(signal, "#8B949E")
    background = SIGNAL_BG.get(signal, "rgba(139, 148, 158, 0.14)")
    label = format_signal(signal)
    return (
        f'<span class="ns-signal-pill" style="background:{background};'
        f"color:{color};border-color:{color}33;\">{label}</span>"
    )


def get_confidence_threshold(risk_profile: str) -> float:
    return {"conservative": 0.5, "aggressive": 0.2}.get(risk_profile, 0.3)


def _conservative_score(signal_row: dict) -> float:
    weights = {"buy": 3, "hold": 2, "strong_buy": 1, "sell": 0, "strong_sell": -1}
    return weights.get(signal_row.get("signal", ""), 0) + signal_row.get("confidence", 0) * 2


def _aggressive_score(signal_row: dict) -> float:
    weights = {"strong_buy": 4, "strong_sell": 3, "buy": 2, "sell": 1, "hold": 0}
    return weights.get(signal_row.get("signal", ""), 0) + signal_row.get("confidence", 0) * 2


def personalize_signals(signals: list[dict], risk_profile: str) -> list[dict]:
    if risk_profile == "conservative":
        return sorted(signals, key=_conservative_score, reverse=True)
    if risk_profile == "aggressive":
        return sorted(signals, key=_aggressive_score, reverse=True)
    return signals


def get_position_size_hint(risk_profile: str, signal: str) -> str:
    hints = {
        "conservative": {"buy": "2-3% of portfolio", "strong_buy": "3-5% of portfolio"},
        "moderate": {"buy": "3-5% of portfolio", "strong_buy": "5-8% of portfolio"},
        "aggressive": {"buy": "5-8% of portfolio", "strong_buy": "8-12% of portfolio"},
    }
    return hints.get(risk_profile, {}).get(signal, "")


def compute_risk_profile(answers: list[int]) -> tuple[int, str]:
    """Given a list of answer scores, return (total_score, risk_profile)."""
    total = sum(answers)
    if total <= 8:
        return total, "conservative"
    if total <= 12:
        return total, "moderate"
    return total, "aggressive"
