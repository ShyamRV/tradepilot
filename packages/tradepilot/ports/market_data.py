from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..trading import Quote


class MarketDataProvider(Protocol):
    """Normalized quote boundary for simulated or contractually licensed data."""

    @property
    def name(self) -> str: ...

    def quote(self, symbol: str) -> "Quote": ...
