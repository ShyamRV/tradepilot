from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import random

from .bars import Bar
from .exit_plan import ExitPlan


@dataclass(frozen=True)
class TimeMachineResult:
    target_first_pct: Decimal
    stop_first_pct: Decimal
    neither_pct: Decimal
    green_pct: Decimal
    average_r: Decimal
    verdict: str
    seed: int
    replays: int


def _verdict(target_first: float, stop_first: float, target_r: float) -> str:
    decided = target_first + stop_first
    if decided <= 0:
        return "Insufficient decided outcomes"
    share = target_first / decided
    breakeven = 1.0 / (1.0 + target_r)
    delta = (share - breakeven) * 100
    if abs(delta) < 5:
        return "Close to a coin flip" if abs(target_r - 1.0) < 0.01 else "Close to break-even"
    lean = "target" if delta > 0 else "stop"
    strength = "Strongly toward" if abs(delta) >= 15 else "Leans toward"
    return f"{strength} the {lean}"


def run_timemachine(
    plan: ExitPlan,
    sessions: list[tuple[Bar, ...]],
    *,
    entry_bar_index: int,
    replays: int = 1000,
    seed: int = 19,
    until_bar: int | None = None,
) -> TimeMachineResult:
    """Monte Carlo replay of the rest of session from historical same-time bars.

    Simplified adaptation of day-trader-skill timemachine: uses ratio pools from
    prior full sessions. Default 1000 replays for sandbox latency.
    """
    if replays <= 0:
        raise ValueError("replays must be positive")
    full = [session for session in sessions if len(session) > entry_bar_index + 1]
    if len(full) < 5:
        return TimeMachineResult(
            Decimal("0"),
            Decimal("0"),
            Decimal("100"),
            Decimal("0"),
            Decimal("0"),
            "Insufficient history for replay",
            seed,
            replays,
        )
    end = until_bar if until_bar is not None else (plan.flat_by_bar or len(full[0]) - 1)
    pools: dict[int, list[tuple[float, float, float, float]]] = {}
    for session in full:
        for index in range(1, min(len(session), end + 1)):
            prev = float(session[index - 1].close)
            if prev <= 0:
                continue
            bar = session[index]
            pools.setdefault(index, []).append(
                (
                    float(bar.open) / prev,
                    float(bar.high) / prev,
                    float(bar.low) / prev,
                    float(bar.close) / prev,
                )
            )
    rng = random.Random(seed)
    target_first = stop_first = neither = green = 0
    r_sum = 0.0
    risk = float(plan.risk_per_share)
    entry = float(plan.entry)
    stop = float(plan.stop)
    target = float(plan.target)
    for _ in range(replays):
        price = entry
        hit = "neither"
        for index in range(entry_bar_index + 1, end + 1):
            bucket = []
            for offset in (-2, -1, 0, 1, 2):
                bucket.extend(pools.get(index + offset, []))
            if not bucket:
                continue
            o_r, h_r, l_r, c_r = rng.choice(bucket)
            high = price * h_r
            low = price * l_r
            close = price * c_r
            # Stop checked before target (skill rule).
            if low <= stop:
                hit = "stop"
                break
            if high >= target:
                hit = "target"
                break
            price = close
        if hit == "target":
            target_first += 1
            green += 1
            r_sum += 1.0
        elif hit == "stop":
            stop_first += 1
            r_sum -= 1.0
        else:
            neither += 1
            if risk > 0:
                r_sum += (price - entry) / risk
            if price >= entry:
                green += 1
    n = float(replays)
    return TimeMachineResult(
        target_first_pct=Decimal(str(round(100 * target_first / n, 1))),
        stop_first_pct=Decimal(str(round(100 * stop_first / n, 1))),
        neither_pct=Decimal(str(round(100 * neither / n, 1))),
        green_pct=Decimal(str(round(100 * green / n, 1))),
        average_r=Decimal(str(round(r_sum / n, 3))),
        verdict=_verdict(target_first / n, stop_first / n, float(plan.target_r)),
        seed=seed,
        replays=replays,
    )
