from __future__ import annotations

from dataclasses import dataclass

from ..ports.broker import BrokerGateway
from ..ports.market_data import MarketDataProvider
from ..trading import Order, OrderStatus


@dataclass
class ExecutionWorker:
    """Deterministic sandbox submission primitive.

    Queue claiming belongs to the durable adapter. This service makes replay
    safe: the broker receives the order's stable intent ID and must return the
    existing result for duplicate submission.
    """

    broker: BrokerGateway
    market: MarketDataProvider

    def submit(self, order: Order) -> Order:
        if not self.broker.sandbox:
            raise RuntimeError("production broker gateway denied")
        if order.status != OrderStatus.QUEUED:
            raise ValueError("only queued orders can be submitted")
        submitted = order.transition(OrderStatus.SUBMITTED)
        try:
            return self.broker.submit(submitted.request, self.market.quote(submitted.request.symbol))
        except TimeoutError:
            return submitted.transition(OrderStatus.UNKNOWN, reason="provider_timeout_unknown")
