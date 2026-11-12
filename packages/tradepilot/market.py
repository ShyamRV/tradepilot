from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Iterable, Protocol


@dataclass(frozen=True)
class Instrument:
    symbol: str
    isin: str
    exchange: str = "NSE"
    active: bool = True


@dataclass(frozen=True)
class Bar:
    session: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class CorporateAction:
    symbol: str
    ex_date: date
    kind: str
    factor: Decimal


class TradingCalendar:
    def __init__(self, holidays: Iterable[date] = ()) -> None:
        self.holidays = frozenset(holidays)

    def is_session(self, day: date) -> bool:
        return day.weekday() < 5 and day not in self.holidays

    def next_session(self, day: date) -> date:
        candidate = day + timedelta(days=1)
        while not self.is_session(candidate):
            candidate += timedelta(days=1)
        return candidate


class EODProvider(Protocol):
    def bars(self, symbol: str, start: date, end: date) -> tuple[Bar, ...]: ...


class CSVProvider:
    REQUIRED = {"symbol", "date", "open", "high", "low", "close", "volume"}

    def __init__(self, content: str) -> None:
        rows = list(csv.DictReader(io.StringIO(content)))
        if not rows or not self.REQUIRED.issubset(rows[0]):
            raise ValueError("CSV has missing required columns")
        self._rows = rows

    def bars(self, symbol: str, start: date, end: date) -> tuple[Bar, ...]:
        result = []
        for row in self._rows:
            session = date.fromisoformat(row["date"])
            if row["symbol"] == symbol and start <= session <= end:
                result.append(Bar(session, *(Decimal(row[k]) for k in ("open", "high", "low", "close")), int(row["volume"])))
        return tuple(sorted(result, key=lambda b: b.session))


@dataclass(frozen=True)
class Dataset:
    id: str
    symbol: str
    bars: tuple[Bar, ...]
    checksum: str
    created_at: datetime
    status: str = "draft"

    def publish(self) -> "Dataset":
        validate_bars(self.bars)
        return Dataset(self.id, self.symbol, self.bars, self.checksum, self.created_at, "published")


def validate_bars(bars: tuple[Bar, ...], *, expected_through: date | None = None) -> None:
    if not bars:
        raise ValueError("dataset is empty")
    if len({b.session for b in bars}) != len(bars):
        raise ValueError("duplicate sessions")
    if any(b.low > min(b.open, b.close) or b.high < max(b.open, b.close) or b.low > b.high for b in bars):
        raise ValueError("invalid OHLC")
    if any(b.volume < 0 for b in bars):
        raise ValueError("negative volume")
    if expected_through and bars[-1].session < expected_through:
        raise ValueError("stale dataset")


def ingest(symbol: str, bars: Iterable[Bar], idempotency_key: str) -> Dataset:
    immutable = tuple(sorted(bars, key=lambda b: b.session))
    validate_bars(immutable)
    payload = json.dumps([
        [str(b.session), str(b.open), str(b.high), str(b.low), str(b.close), b.volume] for b in immutable
    ], separators=(",", ":"))
    checksum = hashlib.sha256(payload.encode()).hexdigest()
    return Dataset(idempotency_key, symbol, immutable, checksum, datetime.now(timezone.utc))
