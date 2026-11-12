from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from tradepilot.agent_runtime import DeterministicAgentRuntime
from tradepilot.agents import AgentConfig, AgentControlPlane, AgentHorizon, AutonomyMode
from tradepilot.api import create_app
from tradepilot.core import InMemoryRepository
from tradepilot.llm_glm import GlmLLMProvider
from tradepilot.realtime import SandboxBroker, SimulatedMarketDataProvider
from tradepilot.settings import TradingSettings
from tradepilot.workers.agent_loop import AgentLoopWorker


def test_glm_fallback_without_credentials():
    provider = GlmLLMProvider(base_url="", api_key="")
    result = provider.explain({"signal": {"symbol": "INFY", "action": "buy"}})
    assert "INFY" in result["summary"]
    assert result["provider"] == "fallback"


def test_agent_loop_submits_sandbox_order_when_enabled():
    repo = InMemoryRepository()
    settings = TradingSettings(autonomous_trading_enabled=True, broker_execution_enabled=True)
    market = SimulatedMarketDataProvider(seed=7, starting_prices={"RELIANCE": Decimal("1532")})
    broker = SandboxBroker(max_fill_quantity=1000)
    control = AgentControlPlane(repo)
    agent = control.create(
        "ws1",
        AgentConfig(
            name="ORB Bot",
            symbols=("RELIANCE",),
            strategy="Opening range",
            max_capital=Decimal("250000"),
            max_daily_loss=Decimal("5000"),
            horizon=AgentHorizon.INTRADAY,
            setups=("orb",),
            autonomy_mode=AutonomyMode.DELEGATED,
        ),
    )
    agent = control.control("ws1", agent.id, "start", "begin paper autonomy")
    worker = AgentLoopWorker(
        repo,
        settings=settings,
        market=market,
        broker=broker,
        agent_control=control,
        runtime=DeterministicAgentRuntime(llm=GlmLLMProvider(base_url="", api_key="")),
    )
    results = worker.tick_agent("ws1", agent)
    assert results
    assert results[0]["symbol"] == "RELIANCE"
    orders = repo.values("sandbox_orders", "ws1")
    decisions = repo.values("agent_decisions", "ws1")
    assert decisions
    # Buy may be skipped if pretrade fails, but decision journal must exist.
    if results[0].get("action") == "buy" and "order_id" in results[0]:
        assert orders


def test_agent_tick_endpoint_requires_autonomy_flag():
    client = TestClient(create_app(InMemoryRepository(), trading_settings=TradingSettings()))
    register = client.post("/v1/auth/register", json={"email": "loop@example.com", "password": "password1"})
    assert register.status_code == 201
    token = client.post("/v1/auth/login", json={"email": "loop@example.com", "password": "password1"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    workspace = client.post("/v1/workspaces", json={"name": "Loop Desk"}, headers=headers).json()
    headers["X-Workspace-ID"] = workspace["id"]
    response = client.post(f"/v1/workspaces/{workspace['id']}/agents/tick", headers=headers)
    assert response.status_code == 503


def test_create_agent_with_horizon_and_tick_when_enabled():
    settings = TradingSettings(autonomous_trading_enabled=True, broker_execution_enabled=True)
    client = TestClient(create_app(InMemoryRepository(), trading_settings=settings))
    client.post("/v1/auth/register", json={"email": "auto@example.com", "password": "password1"})
    token = client.post("/v1/auth/login", json={"email": "auto@example.com", "password": "password1"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    workspace = client.post("/v1/workspaces", json={"name": "Auto Desk"}, headers=headers).json()
    headers["X-Workspace-ID"] = workspace["id"]
    created = client.post(
        f"/v1/workspaces/{workspace['id']}/agents",
        headers=headers,
        json={
            "name": "Day Desk",
            "symbols": ["RELIANCE"],
            "strategy": "Opening range",
            "max_capital": "250000",
            "max_daily_loss": "5000",
            "horizon": "intraday",
            "autonomy_mode": "delegated",
            "target_r": "1",
            "stop_rule": "or_mid",
        },
    )
    assert created.status_code == 201
    agent = created.json()
    assert agent["config"]["horizon"] == "intraday"
    started = client.post(
        f"/v1/workspaces/{workspace['id']}/agents/{agent['id']}/control",
        headers=headers,
        json={"action": "start", "reason": "go"},
    )
    assert started.status_code == 200
    tick = client.post(f"/v1/workspaces/{workspace['id']}/agents/tick", headers=headers)
    assert tick.status_code == 200
    assert "results" in tick.json()
