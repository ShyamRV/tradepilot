from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from enum import StrEnum

from .trading import OrderRequest, Quote, Side


D = Decimal


@dataclass(frozen=True)
class RiskLimits:
    risk_per_trade: Decimal = D("0.01")
    max_position_fraction: Decimal = D("0.20")
    max_daily_loss: Decimal = D("0.03")
    max_order_value: Decimal = D("250000")
    max_open_orders: int = 20
    max_symbol_position: int = 1000
    max_quote_age_seconds: int = 10


class RiskOutcome(StrEnum):
    ALLOW = "allow"
    REJECT = "reject"


@dataclass(frozen=True)
class PretradeContext:
    equity: Decimal
    cash: Decimal
    daily_pnl: Decimal
    current_position: int = 0
    open_orders: int = 0
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class RiskDecision:
    outcome: RiskOutcome
    reasons: tuple[str, ...]
    reference_price: Decimal
    order_value: Decimal
    formula_version: str = "pretrade-v1"

    @property
    def allowed(self) -> bool:
        return self.outcome == RiskOutcome.ALLOW


def evaluate_pretrade(
    order: OrderRequest,
    quote: Quote,
    context: PretradeContext,
    limits: RiskLimits = RiskLimits(),
) -> RiskDecision:
    """Pure deterministic gate. Every failed rule is returned in stable order."""
    price = quote.ask if order.side == Side.BUY else quote.bid
    value = price * order.quantity
    resulting_position = context.current_position + (order.quantity if order.side == Side.BUY else -order.quantity)
    reasons: list[str] = []
    quote_age = (context.now - quote.as_of).total_seconds()
    if quote_age < 0 or quote_age > limits.max_quote_age_seconds:
        reasons.append("stale_quote")
    if context.equity <= 0:
        reasons.append("equity_non_positive")
    if context.daily_pnl <= -(context.equity * limits.max_daily_loss):
        reasons.append("daily_loss_limit")
    if context.open_orders >= limits.max_open_orders:
        reasons.append("open_order_limit")
    if value > limits.max_order_value:
        reasons.append("order_value_limit")
    if abs(resulting_position) > limits.max_symbol_position:
        reasons.append("symbol_position_limit")
    if order.side == Side.BUY and value + indian_fees("buy", price, order.quantity) > context.cash:
        reasons.append("insufficient_cash")
    if order.side == Side.SELL and order.quantity > max(0, context.current_position):
        reasons.append("insufficient_position")
    return RiskDecision(
        RiskOutcome.REJECT if reasons else RiskOutcome.ALLOW,
        tuple(reasons),
        price,
        value,
    )


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
