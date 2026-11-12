from __future__ import annotations

from decimal import Decimal


D = Decimal


def ema(values: list[Decimal], period: int) -> list[Decimal | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    out: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return out
    seed = sum(values[:period]) / D(period)
    out[period - 1] = seed
    alpha = D(2) / D(period + 1)
    current = seed
    for i in range(period, len(values)):
        current = values[i] * alpha + current * (D(1) - alpha)
        out[i] = current
    return out


def rsi(values: list[Decimal], period: int = 14) -> list[Decimal | None]:
    out: list[Decimal | None] = [None] * len(values)
    if len(values) <= period:
        return out
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gain = sum(max(x, D(0)) for x in deltas[:period]) / D(period)
    loss = sum(max(-x, D(0)) for x in deltas[:period]) / D(period)
    out[period] = D(100) if loss == 0 else D(100) - D(100) / (D(1) + gain / loss)
    for i in range(period + 1, len(values)):
        delta = deltas[i - 1]
        gain = (gain * D(period - 1) + max(delta, D(0))) / D(period)
        loss = (loss * D(period - 1) + max(-delta, D(0))) / D(period)
        out[i] = D(100) if loss == 0 else D(100) - D(100) / (D(1) + gain / loss)
    return out


def macd(values: list[Decimal], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[list[Decimal | None], list[Decimal | None]]:
    fast_line, slow_line = ema(values, fast), ema(values, slow)
    line = [None if f is None or s is None else f - s for f, s in zip(fast_line, slow_line)]
    available = [x for x in line if x is not None]
    signal_values = ema(available, signal)
    signal_line: list[Decimal | None] = [None] * (len(line) - len(available)) + signal_values
    return line, signal_line


def atr(high: list[Decimal], low: list[Decimal], close: list[Decimal], period: int = 14) -> list[Decimal | None]:
    if not (len(high) == len(low) == len(close)):
        raise ValueError("series lengths differ")
    tr = []
    for i in range(len(close)):
        tr.append(high[i] - low[i] if i == 0 else max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))
    return ema(tr, period)
