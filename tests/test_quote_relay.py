from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.core import InMemoryRepository
from tradepilot.quote_relay import QuoteRelay
from tradepilot.settings import TradingSettings


def test_quote_relay_caches_and_fans_out_simulated_quotes():
    relay = QuoteRelay.from_env({"QUOTE_RELAY_PROVIDER": "simulated", "QUOTE_RELAY_SYMBOLS": "AAPL,BINANCE:BTCUSDT"})

    async def exercise() -> None:
        queue = await relay.subscribe()
        first = await asyncio.wait_for(queue.get(), timeout=2)
        assert first["type"] == "quote"
        assert first["quote"]["symbol"] in {"AAPL", "BINANCE:BTCUSDT"}
        snapshot = relay.snapshot()
        assert {item["symbol"] for item in snapshot} == {"AAPL", "BINANCE:BTCUSDT"}
        await relay.unsubscribe(queue)
        await relay.stop()

    asyncio.run(exercise())


def test_relay_http_and_websocket_endpoints_do_not_expose_provider_secrets():
    relay = QuoteRelay.from_env({"QUOTE_RELAY_PROVIDER": "simulated", "FINNHUB_API_KEY": "secret-should-not-leak"})
    client = TestClient(create_app(InMemoryRepository(), trading_settings=TradingSettings(), quote_relay=relay))
    response = client.get("/v1/market/relay/quotes")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "simulated"
    assert "secret-should-not-leak" not in response.text
    assert body["quotes"]
    with client.websocket_connect("/v1/market/relay/stream") as websocket:
        hello = websocket.receive_json()
        assert hello["type"] == "hello"
        assert "secret" not in str(hello).lower()
        message = websocket.receive_json()
        assert message["type"] == "quote"
        assert "last" in message["quote"]
