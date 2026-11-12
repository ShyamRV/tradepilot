from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Callable

from .market import Bar, Dataset, TradingCalendar
from .risk import indian_fees


@dataclass(frozen=True)
class Fill:
    symbol: str
    session: date
    side: str
    quantity: int
    price: Decimal
    fees: Decimal


@dataclass(frozen=True)
class Manifest:
    dataset_checksum: str
    strategy_hash: str
    engine_version: str
    created_at: datetime


@dataclass(frozen=True)
class BacktestResult:
    fills: tuple[Fill, ...]
    cash: Decimal
    position: int
    manifest: Manifest


def manifest(dataset: Dataset, strategy: dict, engine_version: str = "1") -> Manifest:
    strategy_hash = hashlib.sha256(json.dumps(strategy, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return Manifest(dataset.checksum, strategy_hash, engine_version, datetime.now(timezone.utc))


def backtest(
    dataset: Dataset,
    strategy: dict,
    signal: Callable[[int, tuple[Bar, ...]], str | None],
    *,
    initial_cash: Decimal = Decimal("100000"),
    quantity: int = 1,
    calendar: TradingCalendar | None = None,
) -> BacktestResult:
    if dataset.status != "published":
        raise ValueError("only published datasets may be backtested")
    calendar = calendar or TradingCalendar()
    bars_by_day = {bar.session: bar for bar in dataset.bars}
    pending: tuple[str, date] | None = None
    cash, position = initial_cash, 0
    fills: list[Fill] = []
    for i, bar in enumerate(dataset.bars):
        if pending and bar.session == pending[1]:
            side = pending[0]
            qty = quantity if side == "buy" else min(quantity, position)
            if qty:
                fee = indian_fees(side, bar.open, qty)
                cash += (-bar.open * qty - fee) if side == "buy" else (bar.open * qty - fee)
                position += qty if side == "buy" else -qty
                fills.append(Fill(dataset.symbol, bar.session, side, qty, bar.open, fee))
            pending = None
        action = signal(i, dataset.bars)
        if action in {"buy", "sell"}:
            target = calendar.next_session(bar.session)
            if target in bars_by_day:
                pending = (action, target)
    return BacktestResult(tuple(fills), cash, position, manifest(dataset, strategy))


class PaperLedger:
    def __init__(self, starting_cash: Decimal = Decimal("100000")) -> None:
        self.cash = starting_cash
        self.positions: dict[str, int] = {}
        self.fills: list[Fill] = []
        self._fills_by_key: dict[str, Fill] = {}

    def fill(self, key: str, symbol: str, session: date, side: str, quantity: int, price: Decimal) -> Fill:
        if key in self._fills_by_key:
            return self._fills_by_key[key]
        if quantity <= 0 or price <= 0 or side not in {"buy", "sell"}:
            raise ValueError("invalid fill")
        held = self.positions.get(symbol, 0)
        if side == "sell" and quantity > held:
            raise ValueError("insufficient position")
        fee = indian_fees(side, price, quantity)
        total = price * quantity
        if side == "buy" and total + fee > self.cash:
            raise ValueError("insufficient cash")
        self.cash += (-total - fee) if side == "buy" else (total - fee)
        self.positions[symbol] = held + (quantity if side == "buy" else -quantity)
        fill = Fill(symbol, session, side, quantity, price, fee)
        self.fills.append(fill)
        self._fills_by_key[key] = fill
        return fill
