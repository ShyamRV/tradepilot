from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(StrEnum):
    CREATED = "created"
    PREVIEWED = "previewed"
    CONFIRMED = "confirmed"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    QUEUED = "queued"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


TERMINAL_STATUSES = frozenset(
    {OrderStatus.RISK_REJECTED, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}
)
ALLOWED_TRANSITIONS = {
    OrderStatus.CREATED: {
        OrderStatus.PREVIEWED,
        OrderStatus.RISK_REJECTED,
        OrderStatus.ACCEPTED,
        OrderStatus.REJECTED,
    },
    OrderStatus.PREVIEWED: {OrderStatus.CONFIRMED, OrderStatus.RISK_REJECTED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.RISK_APPROVED, OrderStatus.RISK_REJECTED, OrderStatus.CANCELLED},
    OrderStatus.RISK_APPROVED: {OrderStatus.QUEUED, OrderStatus.REJECTED},
    OrderStatus.QUEUED: {OrderStatus.SUBMITTED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
    OrderStatus.SUBMITTED: {OrderStatus.ACCEPTED, OrderStatus.UNKNOWN, OrderStatus.REJECTED},
    OrderStatus.UNKNOWN: {
        OrderStatus.ACCEPTED,
        OrderStatus.PARTIALLY_FILLED,
        OrderStatus.FILLED,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED,
    },
    OrderStatus.ACCEPTED: {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
    OrderStatus.PARTIALLY_FILLED: {OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED, OrderStatus.CANCELLED},
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    as_of: datetime
    sequence: int
    provider: str

    def __post_init__(self) -> None:
        if self.bid <= 0 or self.ask < self.bid or not self.symbol:
            raise ValueError("invalid quote")


@dataclass(frozen=True)
class OrderRequest:
    id: str
    workspace_id: str
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: Decimal | None = None
    agent_id: str | None = None
    created_at: datetime = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if self.quantity <= 0 or not self.symbol.strip():
            raise ValueError("quantity and symbol must be valid")
        if self.order_type == OrderType.LIMIT and (self.limit_price is None or self.limit_price <= 0):
            raise ValueError("limit order requires a positive limit price")


@dataclass(frozen=True)
class Fill:
    id: str
    order_id: str
    quantity: int
    price: Decimal
    occurred_at: datetime
    fees: Decimal = Decimal("0")


@dataclass(frozen=True)
class Order:
    request: OrderRequest
    status: OrderStatus = OrderStatus.CREATED
    filled_quantity: int = 0
    average_fill_price: Decimal | None = None
    fills: tuple[Fill, ...] = ()
    reason: str | None = None
    updated_at: datetime = field(default_factory=utcnow)

    @property
    def remaining_quantity(self) -> int:
        return self.request.quantity - self.filled_quantity

    def transition(self, status: OrderStatus, *, reason: str | None = None) -> "Order":
        if status not in ALLOWED_TRANSITIONS.get(self.status, set()):
            raise ValueError(f"invalid order transition: {self.status} -> {status}")
        return replace(self, status=status, reason=reason, updated_at=utcnow())

    def apply_fill(self, fill: Fill) -> "Order":
        if self.status not in {OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}:
            raise ValueError("order cannot be filled in current state")
        if fill.order_id != self.request.id or fill.quantity <= 0 or fill.quantity > self.remaining_quantity:
            raise ValueError("invalid fill")
        total_qty = self.filled_quantity + fill.quantity
        prior_value = (self.average_fill_price or Decimal("0")) * self.filled_quantity
        average = (prior_value + fill.price * fill.quantity) / Decimal(total_qty)
        status = OrderStatus.FILLED if total_qty == self.request.quantity else OrderStatus.PARTIALLY_FILLED
        return replace(
            self,
            status=status,
            filled_quantity=total_qty,
            average_fill_price=average,
            fills=(*self.fills, fill),
            updated_at=fill.occurred_at,
        )


from .ports.broker import BrokerGateway
from .ports.market_data import MarketDataProvider

__all__ = [
    "BrokerGateway",
    "Fill",
    "MarketDataProvider",
    "Order",
    "OrderRequest",
    "OrderStatus",
    "OrderType",
    "Quote",
    "Side",
]
