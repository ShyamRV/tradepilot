from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.auth import InMemoryAuthProvider
from tradepilot.core import InMemoryRepository
from tradepilot.durable import SqliteAuthProvider, SqliteRepository, build_runtime
from tradepilot.strategy import TEMPLATES


def test_sqlite_survives_reopen(tmp_path: Path):
    db = tmp_path / "tradepilot.sqlite3"
    repo = SqliteRepository(db)
    auth = SqliteAuthProvider(repo)
    user = auth.register("owner@example.com", "correct-horse-battery")
    token = auth.login("owner@example.com", "correct-horse-battery")
    workspace = auth.create_workspace(token, "Desk")
    repo.put("strategies", workspace.id, "ema", {"name": "ema", "spec": TEMPLATES["ema_crossover"]})
    assert repo.ping() is True

    reopened = SqliteRepository(db)
    reauth = SqliteAuthProvider(reopened)
    assert reauth.user_for_token(token).id == user.id
    assert reopened.get("strategies", workspace.id, "ema")["name"] == "ema"
    workspaces = reauth.workspaces(token)
    assert len(workspaces) == 1 and workspaces[0][0].name == "Desk"


def test_sqlite_via_env_and_api_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db = tmp_path / "api.sqlite3"
    monkeypatch.setenv("TRADEPILOT_DB_PATH", str(db))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("TRADEPILOT_ENV", "development")
    repo, auth = build_runtime()
    client = TestClient(create_app(repo, auth))
    password = "correct-horse-battery"
    assert client.post("/v1/auth/register", json={"email": "owner@example.com", "password": password}).status_code == 201
    token = client.post("/v1/auth/login", json={"email": "owner@example.com", "password": password}).json()["access_token"]
    headers = {"authorization": f"Bearer {token}"}
    workspace = client.post("/v1/workspaces", json={"name": "Desk"}, headers=headers).json()
    headers["x-workspace-id"] = workspace["id"]
    strategy = {"name": "ema", "spec": TEMPLATES["ema_crossover"]}
    assert client.post(f"/v1/workspaces/{workspace['id']}/strategies", json=strategy, headers=headers).status_code == 201

    again = TestClient(create_app(SqliteRepository(db), SqliteAuthProvider(SqliteRepository(db))))
    listed = again.get("/v1/workspaces", headers={"authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert listed.json()[0]["workspace"]["name"] == "Desk"
    ready = again.get("/ready")
    assert ready.status_code == 200 and ready.json()["status"] == "ready"
    health = again.get("/health")
    assert health.headers["X-Content-Type-Options"] == "nosniff"
    assert health.headers["X-Frame-Options"] == "DENY"


def test_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TRADEPILOT_RATE_LIMIT_PER_MINUTE", "3")
    monkeypatch.delenv("TRADEPILOT_DB_PATH", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(create_app(InMemoryRepository(), InMemoryAuthProvider()))
    codes = [client.get("/v1/strategy-templates").status_code for _ in range(5)]
    assert 429 in codes
    assert client.get("/health").status_code == 200


def test_production_refuses_inmemory(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TRADEPILOT_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TRADEPILOT_DB_PATH", raising=False)
    with pytest.raises(RuntimeError, match="production"):
        create_app()
    with pytest.raises(RuntimeError, match="InMemory"):
        create_app(InMemoryRepository(), InMemoryAuthProvider())
