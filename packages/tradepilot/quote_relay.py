from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

logger = logging.getLogger("tradepilot.quote_relay")

Subscriber = Callable[[dict[str, Any]], Awaitable[None]]

DEFAULT_SYMBOLS = (
    "AAPL",
    "MSFT",
    "NVDA",
    "TSLA",
    "BINANCE:BTCUSDT",
    "BINANCE:ETHUSDT",
)


@dataclass
class CachedQuote:
    symbol: str
    last: float
    change_pct: float
    as_of: str
    source: str
    delayed: bool = False


@dataclass
class QuoteRelay:
    """One upstream market socket (or simulator), shared cache, fan-out to browsers.

    API keys stay on the server. Browsers never see Finnhub/Alpaca credentials.
    """

    provider: str = "simulated"
    finnhub_api_key: str = ""
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    _cache: dict[str, CachedQuote] = field(default_factory=dict)
    _subscribers: set[asyncio.Queue[dict[str, Any]]] = field(default_factory=set)
    _task: asyncio.Task[None] | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _seed_prices: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "QuoteRelay":
        env = environ if environ is not None else dict(os.environ)
        finnhub = env.get("FINNHUB_API_KEY", "").strip()
        alpaca_key = env.get("ALPACA_API_KEY", "").strip()
        alpaca_secret = env.get("ALPACA_API_SECRET", "").strip()
        configured = env.get("QUOTE_RELAY_PROVIDER", "").strip().lower()
        if configured:
            provider = configured
        elif finnhub:
            provider = "finnhub"
        elif alpaca_key and alpaca_secret:
            provider = "alpaca"
        else:
            provider = "simulated"
        raw_symbols = env.get("QUOTE_RELAY_SYMBOLS", ",".join(DEFAULT_SYMBOLS))
        symbols = tuple(item.strip() for item in raw_symbols.split(",") if item.strip()) or DEFAULT_SYMBOLS
        return cls(
            provider=provider,
            finnhub_api_key=finnhub,
            alpaca_api_key=alpaca_key,
            alpaca_api_secret=alpaca_secret,
            symbols=symbols,
        )

    def snapshot(self) -> list[dict[str, Any]]:
        if not self._cache:
            self._ensure_seed_cache()
        return [self._as_dict(item) for item in self._cache.values()]

    def get(self, symbol: str) -> dict[str, Any] | None:
        quote = self._cache.get(symbol.upper()) or self._cache.get(symbol)
        return self._as_dict(quote) if quote else None

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        async with self._lock:
            self._subscribers.add(queue)
            await self._ensure_upstream_locked()
        for item in self.snapshot():
            await queue.put({"type": "quote", "quote": item})
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    async def stop(self) -> None:
        async with self._lock:
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._task = None

    async def _ensure_upstream_locked(self) -> None:
        if self._task and not self._task.done():
            return
        self._ensure_seed_cache()
        self._task = asyncio.create_task(self._run_upstream(), name="quote-relay-upstream")

    def _ensure_seed_cache(self) -> None:
        seeds = {
            "AAPL": 228.4,
            "MSFT": 428.1,
            "NVDA": 131.2,
            "TSLA": 248.6,
            "BINANCE:BTCUSDT": 67_450.0,
            "BINANCE:ETHUSDT": 3_280.0,
        }
        now = _utc_now()
        for symbol in self.symbols:
            if symbol in self._cache:
                continue
            base = seeds.get(symbol, 100.0 + random.random() * 40)
            self._seed_prices[symbol] = base
            self._cache[symbol] = CachedQuote(
                symbol=symbol,
                last=round(base, 4),
                change_pct=0.0,
                as_of=now,
                source="simulated",
                delayed=False,
            )

    async def _run_upstream(self) -> None:
        while True:
            try:
                if self.provider == "finnhub" and self.finnhub_api_key:
                    await self._run_finnhub()
                elif self.provider == "alpaca" and self.alpaca_api_key and self.alpaca_api_secret:
                    await self._run_alpaca()
                else:
                    await self._run_simulated()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - keep relay alive for browsers
                logger.exception("quote relay upstream failed; falling back to simulator briefly")
                await self._run_simulated(seconds=8)

    async def _run_simulated(self, seconds: float | None = None) -> None:
        started = time.monotonic()
        while seconds is None or time.monotonic() - started < seconds:
            for symbol in self.symbols:
                previous = self._cache.get(symbol)
                base = self._seed_prices.get(symbol, previous.last if previous else 100.0)
                last = max(0.01, base * (1 + (random.random() - 0.5) * 0.0012))
                self._seed_prices[symbol] = last
                change = ((last - base) / base) * 100 if base else 0.0
                await self._publish(
                    CachedQuote(
                        symbol=symbol,
                        last=round(last, 4),
                        change_pct=round(change, 4),
                        as_of=_utc_now(),
                        source="simulated",
                        delayed=False,
                    )
                )
            await asyncio.sleep(1.0)

    async def _run_finnhub(self) -> None:
        try:
            import websockets
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("websockets package required for Finnhub relay") from exc

        url = f"wss://ws.finnhub.io?token={self.finnhub_api_key}"
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as socket:
            for symbol in self.symbols:
                await socket.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            async for raw in socket:
                payload = json.loads(raw)
                if payload.get("type") != "trade":
                    continue
                for trade in payload.get("data") or []:
                    symbol = str(trade.get("s") or "")
                    price = float(trade.get("p") or 0)
                    if not symbol or price <= 0:
                        continue
                    previous = self._cache.get(symbol)
                    base = self._seed_prices.get(symbol) or (previous.last if previous else price)
                    self._seed_prices.setdefault(symbol, base)
                    change = ((price - base) / base) * 100 if base else 0.0
                    await self._publish(
                        CachedQuote(
                            symbol=symbol,
                            last=round(price, 6),
                            change_pct=round(change, 4),
                            as_of=_utc_now(),
                            source="finnhub",
                            delayed=False,
                        )
                    )

    async def _run_alpaca(self) -> None:
        try:
            import websockets
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("websockets package required for Alpaca relay") from exc

        url = "wss://stream.data.alpaca.markets/v2/iex"
        equities = [symbol for symbol in self.symbols if ":" not in symbol]
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as socket:
            await socket.send(
                json.dumps({"action": "auth", "key": self.alpaca_api_key, "secret": self.alpaca_api_secret})
            )
            await socket.recv()
            if equities:
                await socket.send(json.dumps({"action": "subscribe", "trades": equities, "quotes": equities}))
            async for raw in socket:
                messages = json.loads(raw)
                if not isinstance(messages, list):
                    messages = [messages]
                for message in messages:
                    msg_type = message.get("T")
                    symbol = str(message.get("S") or "")
                    if msg_type == "t":
                        price = float(message.get("p") or 0)
                    elif msg_type == "q":
                        bid = float(message.get("bp") or 0)
                        ask = float(message.get("ap") or 0)
                        price = ask or bid
                    else:
                        continue
                    if not symbol or price <= 0:
                        continue
                    previous = self._cache.get(symbol)
                    base = self._seed_prices.get(symbol) or (previous.last if previous else price)
                    self._seed_prices.setdefault(symbol, base)
                    change = ((price - base) / base) * 100 if base else 0.0
                    await self._publish(
                        CachedQuote(
                            symbol=symbol,
                            last=round(price, 6),
                            change_pct=round(change, 4),
                            as_of=_utc_now(),
                            source="alpaca",
                            delayed=False,
                        )
                    )

    async def _publish(self, quote: CachedQuote) -> None:
        self._cache[quote.symbol] = quote
        message = {"type": "quote", "quote": self._as_dict(quote)}
        dead: list[asyncio.Queue[dict[str, Any]]] = []
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    _ = queue.get_nowait()
                    queue.put_nowait(message)
                except Exception:  # noqa: BLE001
                    dead.append(queue)
        for queue in dead:
            self._subscribers.discard(queue)

    @staticmethod
    def _as_dict(quote: CachedQuote) -> dict[str, Any]:
        return {
            "symbol": quote.symbol,
            "last": quote.last,
            "change_pct": quote.change_pct,
            "as_of": quote.as_of,
            "source": quote.source,
            "delayed": quote.delayed,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
