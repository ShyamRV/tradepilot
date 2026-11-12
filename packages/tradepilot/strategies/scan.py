from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .bars import Bar


@dataclass(frozen=True)
class ScanHit:
    symbol: str
    setup: str
    as_of: str
    detail: str
    score: Decimal


def _rsi(closes: list[Decimal], period: int = 14) -> Decimal | None:
    if len(closes) < period + 1:
        return None
    gains = Decimal("0")
    losses = Decimal("0")
    window = closes[-(period + 1) :]
    for prev, cur in zip(window, window[1:]):
        delta = cur - prev
        if delta >= 0:
            gains += delta
        else:
            losses += -delta
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))


def scan_daily_closes(symbol: str, closes: tuple[Decimal, ...], as_of: str) -> tuple[ScanHit, ...]:
    """Pre-market style setups from daily closes (day-trader-skill daily scan cousins)."""
    if len(closes) < 21:
        return ()
    hits: list[ScanHit] = []
    last = closes[-1]
    prior = closes[:-1]
    if last > max(prior[-20:]):
        hits.append(ScanHit(symbol, "breakout_20d", as_of, f"close {last} above prior 20 closes", last))
    if len(closes) >= 16:
        leg = closes[-16:-5]
        flag = closes[-5:]
        if leg[0] > 0 and (leg[-1] - leg[0]) / leg[0] > Decimal("0.10"):
            flag_range = (max(flag) - min(flag)) / max(flag)
            if flag_range <= Decimal("0.05"):
                hits.append(ScanHit(symbol, "bull_flag", as_of, "10d thrust then 5d tight range", last))
    ma20 = sum(closes[-20:]) / Decimal("20")
    if closes[-2] < ma20 <= last:
        hits.append(ScanHit(symbol, "reclaim_ma20", as_of, f"reclaimed MA20 {ma20.quantize(Decimal('0.01'))}", last))
    rsi = _rsi(list(closes))
    if rsi is not None and rsi < 30:
        hits.append(ScanHit(symbol, "oversold", as_of, f"RSI14={rsi.quantize(Decimal('0.01'))}", last))
    if rsi is not None and len(closes) >= 3:
        prev_rsi = _rsi(list(closes[:-1]))
        if prev_rsi is not None and prev_rsi < 30 and last > closes[-2]:
            hits.append(ScanHit(symbol, "oversold_bounce", as_of, "RSI was <30 and close up", last))
    # Longer-horizon swing: close above 50-day average after being below
    if len(closes) >= 51:
        ma50 = sum(closes[-50:]) / Decimal("50")
        if closes[-2] < ma50 <= last:
            hits.append(ScanHit(symbol, "swing_ma50_reclaim", as_of, f"reclaimed MA50 {ma50.quantize(Decimal('0.01'))}", last))
    return tuple(hits)


def opening_range(bars: tuple[Bar, ...], or_minutes: int = 15, interval_minutes: int = 5) -> tuple[Decimal, Decimal] | None:
    needed = max(1, or_minutes // interval_minutes)
    if len(bars) < needed:
        return None
    window = bars[:needed]
    return max(bar.high for bar in window), min(bar.low for bar in window)


def scan_orb(
    symbol: str,
    bars: tuple[Bar, ...],
    *,
    as_of: str,
    or_minutes: int = 15,
    interval_minutes: int = 5,
) -> ScanHit | None:
    """First completed bar close above opening-range high."""
    rng = opening_range(bars, or_minutes=or_minutes, interval_minutes=interval_minutes)
    if rng is None:
        return None
    high, low = rng
    needed = max(1, or_minutes // interval_minutes)
    for bar in bars[needed:]:
        if bar.close > high:
            pct = ((bar.close - high) / high) * Decimal("100")
            return ScanHit(
                symbol,
                "orb",
                as_of,
                f"ORB close {bar.close} above range {low}-{high} (+{pct.quantize(Decimal('0.01'))}%)",
                bar.close,
            )
    return None


def scan_bars(
    symbol: str,
    *,
    intraday: tuple[Bar, ...] | None = None,
    daily_closes: tuple[Decimal, ...] | None = None,
    as_of: str,
    setups: tuple[str, ...] = (),
) -> tuple[ScanHit, ...]:
    wanted = set(setups) if setups else None
    hits: list[ScanHit] = []
    if daily_closes:
        hits.extend(scan_daily_closes(symbol, daily_closes, as_of))
    if intraday:
        orb = scan_orb(symbol, intraday, as_of=as_of)
        if orb:
            hits.append(orb)
    if wanted is not None:
        hits = [hit for hit in hits if hit.setup in wanted]
    return tuple(hits)
