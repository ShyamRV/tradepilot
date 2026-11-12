from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.auth import InMemoryAuthProvider
from tradepilot.core import InMemoryRepository
from tradepilot.messaging import TelegramAdapter, dispatch_outbox
from tradepilot.strategy import TEMPLATES


def dataset_payload(key: str = "import-1"):
    return {
        "symbol": "INFY",
        "idempotency_key": key,
        "bars": [
            {"session": "2026-01-02", "open": "100", "high": "102", "low": "99", "close": "101", "volume": 10},
            {"session": "2026-01-05", "open": "103", "high": "105", "low": "102", "close": "104", "volume": 11},
            {"session": "2026-01-06", "open": "106", "high": "108", "low": "105", "close": "107", "volume": 12},
        ],
    }


def setup_account(client: TestClient, email: str = "owner@example.com"):
    password = "correct-horse-battery"
    assert client.post("/v1/auth/register", json={"email": email, "password": password}).status_code == 201
    token = client.post("/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]
    auth = {"authorization": f"Bearer {token}"}
    workspace = client.post("/v1/workspaces", json={"name": "Desk"}, headers=auth).json()
    headers = {**auth, "x-workspace-id": workspace["id"]}
    return token, workspace["id"], headers


def test_password_sessions_logout_and_no_trusted_identity_headers():
    auth = InMemoryAuthProvider()
    client = TestClient(create_app(InMemoryRepository(), auth))
    token, workspace_id, headers = setup_account(client)
    stored = auth._users["owner@example.com"]
    assert stored[2] != b"correct-horse-battery"
    assert client.get("/v1/workspaces", headers={"x-user-id": "fake"}).status_code == 422
    assert client.get(f"/v1/workspaces/{workspace_id}/datasets", headers=headers).status_code == 200
    assert client.post("/v1/auth/logout", headers={"authorization": f"Bearer {token}"}).status_code == 204
    assert client.get(f"/v1/workspaces/{workspace_id}/datasets", headers=headers).status_code == 401


def test_membership_is_server_verified_and_workspaces_are_isolated():
    repo = InMemoryRepository()
    client = TestClient(create_app(repo))
    _, first_workspace, owner_headers = setup_account(client)
    _, second_workspace, second_headers = setup_account(client, "member@example.com")
    body = {"email": "member@example.com", "role": "member"}
    assert client.post(f"/v1/workspaces/{first_workspace}/members", json=body, headers=owner_headers).status_code == 204
    member_token = second_headers["authorization"]
    member_first = {"authorization": member_token, "x-workspace-id": first_workspace}
    assert client.get(f"/v1/workspaces/{first_workspace}/datasets", headers=member_first).status_code == 200
    spoofed = {"authorization": owner_headers["authorization"], "x-workspace-id": second_workspace}
    assert client.get(f"/v1/workspaces/{first_workspace}/datasets", headers=spoofed).status_code == 403


def test_dataset_strategy_analysis_histories_and_provenance():
    repo = InMemoryRepository()
    client = TestClient(create_app(repo))
    _, workspace, headers = setup_account(client)
    base = f"/v1/workspaces/{workspace}"
    first = client.post(f"{base}/datasets", json=dataset_payload(), headers=headers)
    second = client.post(f"{base}/datasets", json=dataset_payload(), headers=headers)
    assert first.status_code == second.status_code == 201
    assert len(client.get(f"{base}/datasets", headers=headers).json()) == 1
    assert client.post(f"{base}/datasets/import-1/publish", headers=headers).status_code == 200
    strategy = {"name": "ema", "spec": TEMPLATES["ema_crossover"]}
    assert client.post(f"{base}/strategies", json=strategy, headers=headers).status_code == 201
    analysis_body = {"idempotency_key": "analysis-1", "dataset_id": "import-1", "strategy_name": "ema"}
    result = client.post(f"{base}/analyses", json=analysis_body, headers=headers)
    assert result.status_code == 201
    analysis = result.json()
    assert analysis["dataset_checksum"] == first.json()["checksum"]
    assert len(analysis["strategy_hash"]) == 64
    assert analysis["evidence"]["entry"]["ready"] is False
    assert client.post(f"{base}/analyses", json=analysis_body, headers=headers).json()["id"] == "analysis-1"
    assert len(client.get(f"{base}/strategies", headers=headers).json()) == 1
    assert len(client.get(f"{base}/analyses", headers=headers).json()) == 1


def test_paper_next_session_fill_notifications_and_dashboard():
    repo = InMemoryRepository()
    client = TestClient(create_app(repo))
    _, workspace, headers = setup_account(client)
    base = f"/v1/workspaces/{workspace}"
    client.post(f"{base}/datasets", json=dataset_payload(), headers=headers)
    client.post(f"{base}/datasets/import-1/publish", headers=headers)
    order = {
        "idempotency_key": "order-1", "dataset_id": "import-1",
        "signal_session": "2026-01-02", "side": "buy", "quantity": 2,
    }
    fill = client.post(f"{base}/paper/orders", json=order, headers=headers).json()["fill"]
    assert fill["session"] == "2026-01-05" and fill["price"] == 103
    assert len(client.get(f"{base}/paper/orders", headers=headers).json()) == 1
    notice = {"idempotency_key": "notice-1", "chat_id": "42", "text": "Filled"}
    assert client.post(f"{base}/notifications", json=notice, headers=headers).json()["created"] is True
    assert client.post(f"{base}/notifications", json=notice, headers=headers).json()["created"] is False
    assert len(client.get(f"{base}/notifications", headers=headers).json()) == 1
    sent = []
    assert dispatch_outbox(repo, TelegramAdapter(lambda chat, text: sent.append((chat, text)))) == 1
    dashboard = client.get(f"{base}/dashboard", headers=headers).json()
    assert dashboard["workspace"]["name"] == "Desk"
    assert dashboard["portfolio"]["cash"] < 100000
    assert dashboard["history"][0]["price"] == 103
    assert dashboard["watchlist"] == []
    assert client.get("/api/dashboard", headers=headers).json()["workspace"] == dashboard["workspace"]
