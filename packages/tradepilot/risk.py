from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN


D = Decimal


@dataclass(frozen=True)
class RiskLimits:
    risk_per_trade: Decimal = D("0.01")
    max_position_fraction: Decimal = D("0.20")
    max_daily_loss: Decimal = D("0.03")


def position_size(equity: Decimal, entry: Decimal, stop: Decimal, limits: RiskLimits = RiskLimits()) -> int:
    if equity <= 0 or entry <= 0 or stop < 0 or entry == stop:
        raise ValueError("invalid risk inputs")
    by_risk = (equity * limits.risk_per_trade / abs(entry - stop)).to_integral_value(rounding=ROUND_DOWN)
    by_exposure = (equity * limits.max_position_fraction / entry).to_integral_value(rounding=ROUND_DOWN)
    return max(0, int(min(by_risk, by_exposure)))


def can_trade(equity: Decimal, daily_pnl: Decimal, limits: RiskLimits = RiskLimits()) -> bool:
    return equity > 0 and daily_pnl > -(equity * limits.max_daily_loss)


def indian_fees(side: str, price: Decimal, quantity: int) -> Decimal:
    """Approximate NSE equity delivery costs, deterministic and Decimal-only."""
    turnover = price * quantity
    brokerage = D("0")
    stt = turnover * (D("0.001") if side == "sell" else D("0"))
    exchange = turnover * D("0.0000297")
    sebi = turnover * D("0.000001")
    stamp = turnover * (D("0.00015") if side == "buy" else D("0"))
    gst = (brokerage + exchange + sebi) * D("0.18")
    return (brokerage + stt + exchange + sebi + stamp + gst).quantize(D("0.01"))
