from __future__ import annotations

import re

from .monte_carlo import DEFAULT_RISK_FREE_RATE


def _parse_percent(value: object) -> float | None:
    if value is None:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value))
    if not match:
        return None
    return float(match.group(0)) / 100.0


def get_india_risk_free_rate() -> float:
    try:
        from jugaad_data.rbi import RBI

        rates = RBI().current_rates()
    except Exception:
        return DEFAULT_RISK_FREE_RATE

    for key in ("91 day T-bills", "364 day T-bills", "Policy Repo Rate"):
        parsed = _parse_percent(rates.get(key))
        if parsed is not None:
            return parsed
    return DEFAULT_RISK_FREE_RATE
