from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from .bars import Bar
from .scan import opening_range


@dataclass(frozen=True)
class ExitPlan:
    symbol: str
    entry: Decimal
    stop: Decimal
    target: Decimal
    risk_per_share: Decimal
    target_r: Decimal
    stop_rule: str
    flat_by_bar: int | None


def plan_exit(
    symbol: str,
    *,
    entry: Decimal,
    bars: tuple[Bar, ...] | None = None,
    stop_rule: str = "or_mid",
    target_r: Decimal = Decimal("1"),
    stop: Decimal | None = None,
    flat_by_bar: int | None = 75,
    or_minutes: int = 15,
    interval_minutes: int = 5,
) -> ExitPlan:
    """Stop/target planner (day-trader-skill exit cousin). Long side only."""
    if entry <= 0:
        raise ValueError("entry must be positive")
    if target_r <= 0:
        raise ValueError("target_r must be positive")
    if stop is not None:
        stop_px = stop
        rule = "explicit"
    elif stop_rule == "or_mid":
        if not bars:
            raise ValueError("bars required for or_mid stop")
        rng = opening_range(bars, or_minutes=or_minutes, interval_minutes=interval_minutes)
        if rng is None:
            raise ValueError("opening range unavailable")
        high, low = rng
        stop_px = ((high + low) / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        rule = "or_mid"
    elif stop_rule == "prior_low":
        if not bars or len(bars) < 2:
            raise ValueError("bars required for prior_low stop")
        stop_px = min(bar.low for bar in bars[-5:]).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        rule = "prior_low"
    elif stop_rule == "pct":
        stop_px = (entry * Decimal("0.98")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        rule = "pct_2"
    else:
        raise ValueError(f"unsupported stop_rule: {stop_rule}")
    if stop_px >= entry:
        stop_px = (entry * Decimal("0.99")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    risk = entry - stop_px
    target = (entry + risk * target_r).quantize(Decimal("0.01"))
    return ExitPlan(symbol, entry, stop_px, target, risk, target_r, rule, flat_by_bar)
