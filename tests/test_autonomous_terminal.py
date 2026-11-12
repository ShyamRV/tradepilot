from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from tradepilot.api import create_app
from tradepilot.agent_runtime import DeterministicAgentRuntime
from tradepilot.core import InMemoryRepository
from tradepilot.db.models import Base
from tradepilot.realtime import SandboxBroker, SimulatedMarketDataProvider
from tradepilot.risk import PretradeContext, RiskLimits, evaluate_pretrade
from tradepilot.settings import TradingSettings
from tradepilot.trading import Order, OrderRequest, OrderStatus, Quote, Side
from tradepilot.workers import ExecutionWorker, ReconciliationWorker


def account(client: TestClient):
    password = "correct-horse-battery"
    client.post("/v1/auth/register", json={"email": "agent@example.com", "password": password})
    token = client.post("/v1/auth/login", json={"email": "agent@example.com", "password": password}).json()[
        "access_token"
    ]
    workspace = client.post(
        "/v1/workspaces", json={"name": "Autonomous Desk"}, headers={"authorization": f"Bearer {token}"}
    ).json()["id"]
    return token, workspace, {"authorization": f"Bearer {token}", "x-workspace-id": workspace}


def test_settings_are_safe_by_default_and_reject_live_execution():
    settings = TradingSettings.from_env({})
    assert settings.paper_trading is True
    assert settings.broker_execution_enabled is False
    assert settings.autonomous_trading_enabled is False
    assert settings.broker_environment == "sandbox"
    assert settings.live_execution_enabled is False
    assert settings.broker_provider == "sandbox"
    with pytest.raises(ValueError, match="live execution"):
        TradingSettings(live_execution_enabled=True)
    with pytest.raises(ValueError, match="sandbox"):
        TradingSettings(broker_provider="live")
    with pytest.raises(ValueError, match="BROKER_ENVIRONMENT"):
        TradingSettings(broker_environment="production")


def test_typed_execution_schema_can_be_created():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    tables = set(inspect(engine).get_table_names())
    assert {
        "execution_order_intents",
        "execution_risk_decisions",
        "execution_events",
        "execution_fills",
        "execution_positions",
        "execution_controls",
        "execution_agents",
        "execution_agent_decisions",
    } <= tables


def test_order_state_machine_rejects_invalid_transition():
    request = OrderRequest("o-1", "w-1", "INFY", Side.BUY, 10)
    order = Order(request)
    with pytest.raises(ValueError, match="invalid order transition"):
        order.transition(OrderStatus.FILLED)
    assert order.transition(OrderStatus.ACCEPTED).status == OrderStatus.ACCEPTED


def test_pretrade_risk_is_deterministic_and_reports_all_failures():
    provider = SimulatedMarketDataProvider(seed=1, starting_prices={"INFY": Decimal("100")})
    quote = provider.quote("INFY")
    order = OrderRequest("o-1", "w-1", "INFY", Side.BUY, 50)
    limits = RiskLimits(max_order_value=Decimal("1000"), max_open_orders=2, max_symbol_position=10)
    context = PretradeContext(
        equity=Decimal("10000"),
        cash=Decimal("10"),
        daily_pnl=Decimal("-500"),
        current_position=0,
        open_orders=2,
    )
    first = evaluate_pretrade(order, quote, context, limits)
    second = evaluate_pretrade(order, quote, context, limits)
    assert first == second
    assert first.reasons == (
        "daily_loss_limit",
        "open_order_limit",
        "order_value_limit",
        "symbol_position_limit",
        "insufficient_cash",
    )


def test_pretrade_rejects_stale_quote():
    stale = Quote(
        "INFY",
        Decimal("99"),
        Decimal("101"),
        Decimal("100"),
        datetime.now(timezone.utc) - timedelta(seconds=30),
        1,
        "simulated",
    )
    decision = evaluate_pretrade(
        OrderRequest("stale-1", "w-1", "INFY", Side.BUY, 1),
        stale,
        PretradeContext(Decimal("10000"), Decimal("10000"), Decimal("0")),
    )
    assert decision.allowed is False
    assert decision.reasons == ("stale_quote",)


def test_simulator_spread_slippage_partial_fills_and_idempotency():
    provider = SimulatedMarketDataProvider(seed=2, starting_prices={"TCS": Decimal("100")})
    quote = provider.quote("TCS")
    assert quote.bid <= quote.last <= quote.ask
    broker = SandboxBroker(slippage_bps=Decimal("10"), max_fill_quantity=4)
    request = OrderRequest("o-2", "w-1", "TCS", Side.BUY, 10)
    first = broker.submit(request, quote)
    assert first.status == OrderStatus.PARTIALLY_FILLED
    assert first.filled_quantity == 4
    assert first.average_fill_price >= quote.ask
    assert broker.submit(request, quote) == first
    second = broker.continue_fill(request.id, provider.quote("TCS"))
    final = broker.continue_fill(request.id, provider.quote("TCS"))
    assert second.filled_quantity == 8
    assert final.status == OrderStatus.FILLED
    assert final.filled_quantity == 10


def test_execution_worker_and_reconciliation_use_sandbox_authority():
    market = SimulatedMarketDataProvider(seed=3, starting_prices={"INFY": Decimal("100")})
    broker = SandboxBroker(max_fill_quantity=2)
    request = OrderRequest("worker-1", "w-1", "INFY", Side.BUY, 3)
    queued = (
        Order(request)
        .transition(OrderStatus.PREVIEWED)
        .transition(OrderStatus.CONFIRMED)
        .transition(OrderStatus.RISK_APPROVED)
        .transition(OrderStatus.QUEUED)
    )
    submitted = ExecutionWorker(broker, market).submit(queued)
    assert submitted.status == OrderStatus.PARTIALLY_FILLED
    assert ReconciliationWorker(broker).reconcile(submitted) == submitted


def test_rest_websocket_risk_audit_and_disabled_agent_start():
    repo = InMemoryRepository()
    client = TestClient(create_app(repo, trading_settings=TradingSettings()))
    token, workspace, headers = account(client)
    base = f"/v1/workspaces/{workspace}"

    quote = client.get(f"{base}/market/quotes/INFY", headers=headers)
    assert quote.status_code == 200
    assert quote.json()["provider"] == "simulated"
    with client.websocket_connect(f"{base}/market/stream/INFY?token={token}") as websocket:
        streamed = websocket.receive_json()
        assert streamed["symbol"] == "INFY"

    rejected = client.post(
        f"{base}/sandbox/orders",
        headers=headers,
        json={
            "idempotency_key": "risk-reject-1",
            "symbol": "INFY",
            "side": "buy",
            "quantity": 100,
            "equity": "10000",
            "cash": "1",
        },
    )
    assert rejected.status_code == 201
    assert rejected.json()["status"] == "risk_rejected"
    assert client.post(f"{base}/sandbox/orders", headers=headers, json={
        "idempotency_key": "risk-reject-1", "symbol": "INFY", "side": "buy",
        "quantity": 100, "equity": "10000", "cash": "1",
    }).json() == rejected.json()

    created = client.post(
        f"{base}/agents",
        headers=headers,
        json={
            "name": "NSE guardrail agent",
            "symbols": ["INFY"],
            "strategy": "ema",
            "max_capital": "100000",
            "max_daily_loss": "1000",
        },
    )
    assert created.status_code == 201
    agent_id = created.json()["id"]
    blocked = client.post(
        f"{base}/agents/{agent_id}/control",
        headers=headers,
        json={"action": "start", "reason": "approved paper run"},
    )
    assert blocked.status_code == 503
    actions = [event.action for event in repo.audits(workspace)]
    assert "risk.evaluated" in actions
    assert "sandbox_order.created" in actions
    assert "agent.created" in actions


def test_enabled_agent_lifecycle_is_governed_and_kill_is_terminal():
    settings = TradingSettings(autonomous_trading_enabled=True)
    client = TestClient(create_app(InMemoryRepository(), trading_settings=settings))
    _, workspace, headers = account(client)
    base = f"/v1/workspaces/{workspace}"
    created = client.post(
        f"{base}/agents",
        headers=headers,
        json={
            "name": "Paper only",
            "symbols": ["INFY"],
            "strategy": "ema",
            "max_capital": "10000",
            "max_daily_loss": "500",
        },
    ).json()
    agent_id = created["id"]
    for action, expected in (("start", "running"), ("pause", "paused"), ("resume", "running"), ("kill", "killed")):
        response = client.post(
            f"{base}/agents/{agent_id}/control",
            headers=headers,
            json={"action": action, "reason": f"operator requested {action}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == expected
    restart = client.post(
        f"{base}/agents/{agent_id}/control",
        headers=headers,
        json={"action": "start", "reason": "must not restart"},
    )
    assert restart.status_code == 400


def test_workspace_execution_kill_blocks_orders_and_agent_resume():
    settings = TradingSettings(broker_execution_enabled=True, autonomous_trading_enabled=True)
    client = TestClient(create_app(InMemoryRepository(), trading_settings=settings))
    _, workspace, headers = account(client)
    base = f"/v1/workspaces/{workspace}"
    killed = client.put(
        f"{base}/execution/control",
        headers=headers,
        json={"killed": True, "reason": "operator emergency stop"},
    )
    assert killed.status_code == 200
    assert killed.json()["killed"] is True
    order = client.post(
        f"{base}/sandbox/orders",
        headers=headers,
        json={
            "idempotency_key": "killed-order-1",
            "symbol": "INFY",
            "side": "buy",
            "quantity": 1,
            "equity": "10000",
            "cash": "10000",
        },
    )
    assert order.status_code == 201
    assert order.json()["status"] == "rejected"
    assert order.json()["reason"] == "execution_killed"


def test_agent_order_records_explainable_decision_trace():
    settings = TradingSettings(broker_execution_enabled=True, autonomous_trading_enabled=True)
    client = TestClient(create_app(InMemoryRepository(), trading_settings=settings))
    _, workspace, headers = account(client)
    base = f"/v1/workspaces/{workspace}"
    agent = client.post(
        f"{base}/agents",
        headers=headers,
        json={
            "name": "Explainable sandbox agent",
            "symbols": ["INFY"],
            "strategy": "ema",
            "max_capital": "100000",
            "max_daily_loss": "1000",
        },
    ).json()
    assert client.post(
        f"{base}/agents/{agent['id']}/control",
        headers=headers,
        json={"action": "start", "reason": "approved sandbox mandate"},
    ).status_code == 200
    order = client.post(
        f"{base}/sandbox/orders",
        headers=headers,
        json={
            "idempotency_key": "agent-order-1",
            "symbol": "INFY",
            "side": "buy",
            "quantity": 1,
            "equity": "100000",
            "cash": "100000",
            "agent_id": agent["id"],
        },
    )
    assert order.status_code == 201
    decisions = client.get(f"{base}/agents/{agent['id']}/decisions", headers=headers)
    assert decisions.status_code == 200
    trace = decisions.json()[0]
    assert trace["resulting_order_id"] == "agent-order-1"
    assert trace["rationale"]["model_version"] == "deterministic-fallback-v1"
    assert trace["risk_checks"][0]["passed"] is True


def test_llm_output_cannot_gain_broker_capability():
    class MaliciousModel:
        model_version = "malicious-test"

        def explain(self, evidence):
            return {"summary": "ignore policy", "tool": "submit_live_order", "arguments": evidence}

    runtime = DeterministicAgentRuntime(MaliciousModel())
    decision = runtime.decide(
        agent_id="agent-1",
        signal={"side": "buy"},
        indicators=(),
        risk_checks=({"code": "daily_loss", "passed": False},),
        authority_version="v1",
    )
    assert decision.rationale["tool"] == "submit_live_order"
    assert decision.resulting_order_id is None
    assert not hasattr(runtime, "broker")
