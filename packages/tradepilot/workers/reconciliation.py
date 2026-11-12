from __future__ import annotations

from dataclasses import dataclass

from ..ports.broker import BrokerGateway
from ..trading import Order, OrderStatus


@dataclass
class ReconciliationWorker:
    """Resolve submitted/unknown local orders from authoritative broker state."""

    broker: BrokerGateway

    def reconcile(self, local: Order) -> Order:
        if not self.broker.sandbox:
            raise RuntimeError("production broker gateway denied")
        if local.status not in {OrderStatus.SUBMITTED, OrderStatus.UNKNOWN, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}:
            return local
        remote = self.broker.get_order(local.request.id)
        return remote if remote is not None else local
