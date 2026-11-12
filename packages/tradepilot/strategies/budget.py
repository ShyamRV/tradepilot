from __future__ import annotations

from decimal import Decimal, ROUND_DOWN


def size_from_max_loss(
    *,
    entry: Decimal,
    stop: Decimal,
    max_loss: Decimal,
    max_capital: Decimal,
    max_shares: int = 100_000,
) -> int:
    """Position size from max loss per trade (day-trader-skill budget rule)."""
    if entry <= 0 or stop < 0 or entry == stop:
        raise ValueError("invalid entry/stop")
    if max_loss <= 0 or max_capital <= 0:
        raise ValueError("invalid capital limits")
    risk = abs(entry - stop)
    by_loss = (max_loss / risk).to_integral_value(rounding=ROUND_DOWN)
    by_capital = (max_capital / entry).to_integral_value(rounding=ROUND_DOWN)
    return max(0, int(min(by_loss, by_capital, Decimal(max_shares))))
