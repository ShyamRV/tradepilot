from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from .bars import Bar
from .scan import opening_range


class EntryStatus(StrEnum):
    WAITING = "waiting"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    NOT_OPEN = "not_open"


@dataclass(frozen=True)
class EntrySignal:
    symbol: str
    setup: str
    status: EntryStatus
    price: Decimal | None
    level: Decimal | None
    bar_index: int | None
    message: str


def evaluate_entry(
    symbol: str,
    bars: tuple[Bar, ...],
    *,
    setup: str = "orb",
    level: Decimal | None = None,
    or_minutes: int = 15,
    interval_minutes: int = 5,
    no_entries_after_bar: int | None = None,
) -> EntrySignal:
    """Bar-close entry timer (day-trader-skill entry.py rule, long only)."""
    if not bars:
        return EntrySignal(symbol, setup, EntryStatus.NOT_OPEN, None, None, None, "no bars")
    if setup == "orb":
        rng = opening_range(bars, or_minutes=or_minutes, interval_minutes=interval_minutes)
        if rng is None:
            return EntrySignal(symbol, setup, EntryStatus.NOT_OPEN, None, None, None, "opening range incomplete")
        high, _low = rng
        trigger_level = high
        start_index = max(1, or_minutes // interval_minutes)
    elif setup == "level":
        if level is None:
            raise ValueError("level required for level setup")
        trigger_level = level
        start_index = 0
    else:
        raise ValueError(f"unsupported entry setup: {setup}")

    cutoff = no_entries_after_bar if no_entries_after_bar is not None else len(bars)
    last = bars[min(len(bars), cutoff) - 1]
    for index, bar in enumerate(bars[start_index:cutoff], start=start_index):
        if bar.close > trigger_level:
            return EntrySignal(
                symbol,
                setup,
                EntryStatus.TRIGGERED,
                bar.close,
                trigger_level,
                index,
                f"triggered at bar {index} close {bar.close} above {trigger_level}",
            )
    distance = trigger_level - last.close
    if cutoff < len(bars) and last.close <= trigger_level:
        return EntrySignal(
            symbol,
            setup,
            EntryStatus.EXPIRED,
            last.close,
            trigger_level,
            None,
            "entry window expired without trigger",
        )
    return EntrySignal(
        symbol,
        setup,
        EntryStatus.WAITING,
        last.close,
        trigger_level,
        None,
        f"waiting; last close {last.close} is {distance.quantize(Decimal('0.01'))} under {trigger_level}",
    )
