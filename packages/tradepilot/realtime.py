from __future__ import annotations

import random
import threading
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from .risk import indian_fees
from .trading import Fill, Order, OrderRequest, OrderStatus, OrderType, Quote, Side


class SimulatedMarketDataProvider:
    """Deterministic in-process quote source suitable only for sandbox use."""

    name = "simulated"

    def __init__(
        self,
        *,
        seed: int = 7,
        spread_bps: Decimal = Decimal("5"),
        starting_prices: dict[str, Decimal] | None = None,
    ) -> None:
        self._random = random.Random(seed)
        self._spread_bps = spread_bps
        self._prices = {key.upper(): value for key, value in (starting_prices or {}).items()}
        self._sequences: dict[str, int] = {}
        self._lock = threading.RLock()

    def quote(self, symbol: str) -> Quote:
        stable = symbol.strip().upper()
        if not stable:
            raise ValueError("symbol required")
        with self._lock:
            last = self._prices.get(stable, Decimal("100"))
            movement_bps = Decimal(str(self._random.randint(-20, 20)))
            last = max(Decimal("0.01"), last * (Decimal("1") + movement_bps / Decimal("10000")))
            last = last.quantize(Decimal("0.01"))
            half_spread = last * self._spread_bps / Decimal("20000")
            bid = (last - half_spread).quantize(Decimal("0.01"))
            ask = (last + half_spread).quantize(Decimal("0.01"))
            sequence = self._sequences.get(stable, 0) + 1
            self._prices[stable], self._sequences[stable] = last, sequence
            return Quote(stable, bid, ask, last, datetime.now(timezone.utc), sequence, self.name)


class SandboxBroker:
    name = "sandbox"
    sandbox = True

    def __init__(self, *, slippage_bps: Decimal = Decimal("2"), max_fill_quantity: int = 25) -> None:
        if slippage_bps < 0 or max_fill_quantity <= 0:
            raise ValueError("invalid sandbox broker settings")
        self.slippage_bps = slippage_bps
        self.max_fill_quantity = max_fill_quantity
        self._orders: dict[str, Order] = {}
        self._lock = threading.RLock()

    def submit(self, request: OrderRequest, quote: Quote) -> Order:
        with self._lock:
            if request.id in self._orders:
                return self._orders[request.id]
            order = Order(request).transition(OrderStatus.ACCEPTED)
            executable = (
                request.order_type == OrderType.MARKET
                or request.side == Side.BUY and request.limit_price is not None and request.limit_price >= quote.ask
                or request.side == Side.SELL and request.limit_price is not None and request.limit_price <= quote.bid
            )
            if executable:
                quantity = min(request.quantity, self.max_fill_quantity)
                touch = quote.ask if request.side == Side.BUY else quote.bid
                direction = Decimal("1") if request.side == Side.BUY else Decimal("-1")
                price = (touch * (Decimal("1") + direction * self.slippage_bps / Decimal("10000"))).quantize(
                    Decimal("0.01")
                )
                fill = Fill(
                    id=str(uuid4()),
                    order_id=request.id,
                    quantity=quantity,
                    price=price,
                    occurred_at=datetime.now(timezone.utc),
                    fees=indian_fees(request.side.value, price, quantity),
                )
                order = order.apply_fill(fill)
            self._orders[request.id] = order
            return order

    def continue_fill(self, order_id: str, quote: Quote) -> Order:
        with self._lock:
            order = self._orders[order_id]
            if order.status != OrderStatus.PARTIALLY_FILLED:
                return order
            quantity = min(order.remaining_quantity, self.max_fill_quantity)
            touch = quote.ask if order.request.side == Side.BUY else quote.bid
            direction = Decimal("1") if order.request.side == Side.BUY else Decimal("-1")
            price = (touch * (Decimal("1") + direction * self.slippage_bps / Decimal("10000"))).quantize(
                Decimal("0.01")
            )
            fill = Fill(
                str(uuid4()), order_id, quantity, price, datetime.now(timezone.utc),
                indian_fees(order.request.side.value, price, quantity),
            )
            order = order.apply_fill(fill)
            self._orders[order_id] = order
            return order

    def cancel(self, order_id: str) -> Order:
        with self._lock:
            order = self._orders[order_id]
            order = order.transition(OrderStatus.CANCELLED)
            self._orders[order_id] = order
            return order

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)
