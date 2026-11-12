from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
import random


@dataclass(frozen=True)
class Bar:
    start: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def _d(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def synthesize_session_bars(
    *,
    symbol: str,
    base_price: Decimal,
    seed: int,
    bars: int = 78,
    interval_minutes: int = 5,
    session_start: datetime | None = None,
) -> tuple[Bar, ...]:
    """Build a full cash-session style bar series for sandbox / offline tests.

    Mimics the day-trader-skill 5m NYSE shape (78 bars) but is market-agnostic —
    callers pin session_start for IST or ET as needed.
    """
    rng = random.Random(f"{seed}:{symbol.upper()}")
    start = session_start or datetime(2026, 10, 19, 9, 30, tzinfo=timezone.utc)
    price = float(base_price)
    out: list[Bar] = []
    for index in range(bars):
        drift = math.sin(index / 7.0) * 0.0015 + (rng.random() - 0.5) * 0.002
        open_px = price
        close_px = max(0.05, price * (1 + drift))
        # Deterministic opening-range breakout after the first 15m (bar 8 ≈ 10:10–10:15).
        if index == 8 and out:
            range_high = max(bar.high for bar in out[:3])
            close_px = float(range_high) * 1.006
            open_px = float(range_high) * 1.001
        high_px = max(open_px, close_px) * (1 + rng.random() * 0.001)
        low_px = min(open_px, close_px) * (1 - rng.random() * 0.001)
        volume = 20_000 + int(rng.random() * 80_000)
        out.append(
            Bar(
                start=start + timedelta(minutes=interval_minutes * index),
                open=_d(open_px),
                high=_d(high_px),
                low=_d(low_px),
                close=_d(close_px),
                volume=volume,
            )
        )
        price = close_px
    return tuple(out)


def daily_closes_from_sessions(sessions: list[tuple[Bar, ...]]) -> tuple[Decimal, ...]:
    return tuple(session[-1].close for session in sessions if session)
