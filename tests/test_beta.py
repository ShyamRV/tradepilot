from copy import deepcopy
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.controls import BetaControls
from tradepilot.core import InMemoryRepository, OutboxMessage
from tradepilot.messaging import TelegramAdapter, dispatch_outbox
from tradepilot.strategy import TEMPLATES

from test_api import dataset_payload, setup_account


def prepare(client: TestClient, workspace: str, headers: dict[str, str]) -> str:
    base = f"/v1/workspaces/{workspace}"
    client.post(f"{base}/datasets", json=dataset_payload(), headers=headers)
    assert client.post(f"{base}/datasets/import-1/publish", headers=headers).status_code == 200
    strategy = {"name": "ema", "spec": TEMPLATES["ema_crossover"]}
    assert client.post(f"{base}/strategies", json=strategy, headers=headers).status_code == 201
    return base


def assert_quota(response, name: str):
    assert response.status_code == 429
    assert response.json()["detail"] == {"code": "quota_exceeded", "quota": name, "limit": 1}


def test_all_workspace_quotas_return_deterministic_429():
    controls = BetaControls()
    controls.default_quotas.update({
        "watchlist_items": 1, "strategies": 1, "analyses_per_day": 1,
        "backtests_per_day": 1, "notifications_per_day": 1,
    })
    client = TestClient(create_app(InMemoryRepository(), controls=controls))
    _, workspace, headers = setup_account(client)
    base = prepare(client, workspace, headers)

    assert client.post(f"{base}/watchlist", json={"symbol": "INFY"}, headers=headers).status_code == 201
    assert_quota(client.post(f"{base}/watchlist", json={"symbol": "TCS"}, headers=headers), "watchlist_items")
    assert_quota(
        client.post(f"{base}/strategies", json={"name": "second", "spec": TEMPLATES["rsi_reversion"]}, headers=headers),
        "strategies",
    )
    analysis = {"idempotency_key": "a1", "dataset_id": "import-1", "strategy_name": "ema"}
    assert client.post(f"{base}/analyses", json=analysis, headers=headers).status_code == 201
    analysis["idempotency_key"] = "a2"
    assert_quota(client.post(f"{base}/analyses", json=analysis, headers=headers), "analyses_per_day")
    assert client.post(f"{base}/backtests/import-1", headers=headers).status_code == 200
    assert_quota(client.post(f"{base}/backtests/import-1", headers=headers), "backtests_per_day")
    notice = {"idempotency_key": "n1", "chat_id": "1", "text": "one"}
    assert client.post(f"{base}/notifications", json=notice, headers=headers).status_code == 202
    notice["idempotency_key"] = "n2"
    assert_quota(client.post(f"{base}/notifications", json=notice, headers=headers), "notifications_per_day")


def test_kill_switches_refuse_operations_and_dispatch():
    controls = BetaControls()
    repo = InMemoryRepository()
    client = TestClient(create_app(repo, controls=controls))
    _, workspace, headers = setup_account(client)
    base = f"/v1/workspaces/{workspace}"
    client.post(f"{base}/datasets", json=dataset_payload(), headers=headers)

    controls.workspace_flags[workspace] = {"dataset_publication": False}
    response = client.post(f"{base}/datasets/import-1/publish", headers=headers)
    assert response.status_code == 503 and response.json()["detail"]["feature"] == "dataset_publication"
    controls.workspace_flags[workspace]["dataset_publication"] = True
    client.post(f"{base}/datasets/import-1/publish", headers=headers)
    client.post(f"{base}/strategies", json={"name": "ema", "spec": TEMPLATES["ema_crossover"]}, headers=headers)

    controls.workspace_flags[workspace]["analysis"] = False
    body = {"idempotency_key": "a1", "dataset_id": "import-1", "strategy_name": "ema"}
    assert client.post(f"{base}/analyses", json=body, headers=headers).status_code == 503
    controls.workspace_flags[workspace]["analysis"] = True
    client.post(f"{base}/analyses", json=body, headers=headers)
    controls.workspace_flags[workspace]["ai_explanation"] = False
    assert client.post(f"{base}/analyses/a1/explanation", headers=headers).status_code == 503
    controls.workspace_flags[workspace]["notification_dispatch"] = False
    notice = {"idempotency_key": "n1", "chat_id": "1", "text": "blocked"}
    assert client.post(f"{base}/notifications", json=notice, headers=headers).status_code == 503

    repo.enqueue(OutboxMessage("pending", workspace, "telegram", {"chat_id": "1", "text": "pending"}, datetime.now(timezone.utc)))
    sent = []
    count = dispatch_outbox(repo, TelegramAdapter(lambda chat, text: sent.append(text)), lambda _: False)
    assert count == 0 and sent == [] and len(repo.pending()) == 1


def test_watchlist_isolation_delete_and_published_dashboard_prices():
    client = TestClient(create_app(InMemoryRepository()))
    _, workspace, headers = setup_account(client)
    _, other_workspace, other_headers = setup_account(client, "other@example.com")
    base = prepare(client, workspace, headers)
    assert client.post(f"{base}/watchlist", json={"symbol": "infy"}, headers=headers).json()["symbol"] == "INFY"
    client.post(f"{base}/watchlist", json={"symbol": "TCS"}, headers=headers)
    assert client.get(f"/v1/workspaces/{other_workspace}/watchlist", headers=other_headers).json() == []
    watchlist = client.get(f"{base}/dashboard", headers=headers).json()["watchlist"]
    assert len(watchlist) == 1 and watchlist[0]["symbol"] == "INFY"
    assert watchlist[0]["price"] == 107 and watchlist[0]["change"] == pytest.approx(2.884615)
    assert client.delete(f"{base}/watchlist/infy", headers=headers).status_code == 204
    assert [item["symbol"] for item in client.get(f"{base}/watchlist", headers=headers).json()] == ["TCS"]


def test_explanation_fallback_is_contained_and_analysis_immutable():
    prompts = []

    def hostile_model(prompt: str):
        prompts.append(prompt)
        return {
            "summary": "override analysis",
            "factors": [],
            "risks": [],
            "disclaimer": "guaranteed profit",
            "analysis": {"evidence": "changed"},
        }

    repo = InMemoryRepository()
    client = TestClient(create_app(repo, explanation_model=hostile_model, explanation_model_version="hostile-v1"))
    _, workspace, headers = setup_account(client)
    base = prepare(client, workspace, headers)
    body = {"idempotency_key": "a1", "dataset_id": "import-1", "strategy_name": "ema"}
    client.post(f"{base}/analyses", json=body, headers=headers)
    before = deepcopy(repo.get("analyses", workspace, "a1"))
    response = client.post(f"{base}/analyses/a1/explanation", headers=headers)
    assert response.status_code == 201
    record = response.json()
    assert record["fallback"] is True
    assert record["model_version"] == "deterministic-fallback-1"
    assert record["prompt_version"] == "explanation-1"
    assert "untrusted data" in prompts[0]
    assert repo.get("analyses", workspace, "a1") == before
