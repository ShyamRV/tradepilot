from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..trading import Order, OrderRequest, Quote


class BrokerGateway(Protocol):
    """Normalized broker boundary. Implementations must identify sandbox state."""

    @property
    def name(self) -> str: ...

    @property
    def sandbox(self) -> bool: ...

    def submit(self, request: "OrderRequest", quote: "Quote") -> "Order": ...

    def cancel(self, order_id: str) -> "Order": ...

    def get_order(self, order_id: str) -> "Order | None": ...
