from __future__ import annotations

import hashlib
import hmac
import json
import os
import pickle
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from .auth import AuthenticationError, AuthProvider, User, Workspace
from .core import AuditEvent, ForbiddenError, OutboxMessage, Principal


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SqliteRepository:
    """File-backed repository. Survives process restarts."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS kv (
                  bucket TEXT NOT NULL,
                  tenant_id TEXT NOT NULL,
                  key TEXT NOT NULL,
                  value BLOB NOT NULL,
                  PRIMARY KEY (bucket, tenant_id, key)
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                  id TEXT PRIMARY KEY,
                  tenant_id TEXT NOT NULL,
                  actor_id TEXT NOT NULL,
                  action TEXT NOT NULL,
                  resource TEXT NOT NULL,
                  occurred_at TEXT NOT NULL,
                  detail TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS outbox (
                  id TEXT PRIMARY KEY,
                  tenant_id TEXT NOT NULL,
                  topic TEXT NOT NULL,
                  payload TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  sent INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS users (
                  id TEXT PRIMARY KEY,
                  email TEXT NOT NULL UNIQUE,
                  salt BLOB NOT NULL,
                  password_hash BLOB NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                  token_hash TEXT PRIMARY KEY,
                  user_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS workspaces (
                  id TEXT PRIMARY KEY,
                  name TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memberships (
                  workspace_id TEXT NOT NULL,
                  user_id TEXT NOT NULL,
                  role TEXT NOT NULL,
                  PRIMARY KEY (workspace_id, user_id)
                );
                """
            )

    def ping(self) -> bool:
        with self._lock, self._connect() as conn:
            conn.execute("SELECT 1")
        return True

    def append_audit(self, event: AuditEvent) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO audit_events(id, tenant_id, actor_id, action, resource, occurred_at, detail) VALUES (?,?,?,?,?,?,?)",
                (
                    event.id,
                    event.tenant_id,
                    event.actor_id,
                    event.action,
                    event.resource,
                    event.occurred_at.isoformat(),
                    json.dumps(event.detail),
                ),
            )

    def audits(self, tenant_id: str) -> tuple[AuditEvent, ...]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_events WHERE tenant_id = ? ORDER BY occurred_at",
                (tenant_id,),
            ).fetchall()
        return tuple(
            AuditEvent(
                id=row["id"],
                tenant_id=row["tenant_id"],
                actor_id=row["actor_id"],
                action=row["action"],
                resource=row["resource"],
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
                detail=json.loads(row["detail"]),
            )
            for row in rows
        )

    def put(self, bucket: str, tenant_id: str, key: str, value: Any) -> bool:
        payload = pickle.dumps(value, protocol=4)
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO kv(bucket, tenant_id, key, value) VALUES (?,?,?,?)",
                    (bucket, tenant_id, key, payload),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def replace(self, bucket: str, tenant_id: str, key: str, value: Any) -> None:
        payload = pickle.dumps(value, protocol=4)
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "UPDATE kv SET value = ? WHERE bucket = ? AND tenant_id = ? AND key = ?",
                (payload, bucket, tenant_id, key),
            )
            if cur.rowcount == 0:
                raise KeyError(key)

    def get(self, bucket: str, tenant_id: str, key: str) -> Any | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM kv WHERE bucket = ? AND tenant_id = ? AND key = ?",
                (bucket, tenant_id, key),
            ).fetchone()
        return pickle.loads(row["value"]) if row else None

    def values(self, bucket: str, tenant_id: str) -> tuple[Any, ...]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT value FROM kv WHERE bucket = ? AND tenant_id = ?",
                (bucket, tenant_id),
            ).fetchall()
        return tuple(pickle.loads(row["value"]) for row in rows)

    def delete(self, bucket: str, tenant_id: str, key: str) -> bool:
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM kv WHERE bucket = ? AND tenant_id = ? AND key = ?",
                (bucket, tenant_id, key),
            )
            return cur.rowcount > 0

    def enqueue(self, message: OutboxMessage) -> bool:
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO outbox(id, tenant_id, topic, payload, created_at, sent) VALUES (?,?,?,?,?,0)",
                    (
                        message.id,
                        message.tenant_id,
                        message.topic,
                        json.dumps(message.payload),
                        message.created_at.isoformat(),
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def pending(self) -> tuple[OutboxMessage, ...]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM outbox WHERE sent = 0 ORDER BY created_at"
            ).fetchall()
        return tuple(
            OutboxMessage(
                id=row["id"],
                tenant_id=row["tenant_id"],
                topic=row["topic"],
                payload=json.loads(row["payload"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        )

    def mark_sent(self, message_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE outbox SET sent = 1 WHERE id = ?", (message_id,))


class SqliteAuthProvider:
    ROLES = {"owner", "publisher", "auditor", "member"}

    def __init__(self, repository: SqliteRepository) -> None:
        self.repo = repository

    @staticmethod
    def _password_hash(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    @staticmethod
    def _session_key(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def register(self, email: str, password: str) -> User:
        normalized = email.strip().lower()
        if "@" not in normalized or len(password) < 12:
            raise AuthenticationError("valid email and password of at least 12 characters required")
        salt = secrets.token_bytes(16)
        user = User(str(uuid4()), normalized)
        with self.repo._lock, self.repo._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO users(id, email, salt, password_hash) VALUES (?,?,?,?)",
                    (user.id, normalized, salt, self._password_hash(password, salt)),
                )
            except sqlite3.IntegrityError as exc:
                raise AuthenticationError("account already exists") from exc
        return user

    def login(self, email: str, password: str) -> str:
        with self.repo._lock, self.repo._connect() as conn:
            row = conn.execute(
                "SELECT id, salt, password_hash FROM users WHERE email = ?",
                (email.strip().lower(),),
            ).fetchone()
            if not row or not hmac.compare_digest(
                row["password_hash"], self._password_hash(password, row["salt"])
            ):
                raise AuthenticationError("invalid credentials")
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO sessions(token_hash, user_id, created_at) VALUES (?,?,?)",
                (self._session_key(token), row["id"], _utcnow().isoformat()),
            )
        return token

    def logout(self, token: str) -> None:
        with self.repo._lock, self.repo._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (self._session_key(token),))

    def user_for_token(self, token: str) -> User:
        with self.repo._lock, self.repo._connect() as conn:
            row = conn.execute(
                """
                SELECT u.id, u.email FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ?
                """,
                (self._session_key(token),),
            ).fetchone()
        if not row:
            raise AuthenticationError("invalid or expired session")
        return User(row["id"], row["email"])

    def create_workspace(self, token: str, name: str) -> Workspace:
        user = self.user_for_token(token)
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("workspace name required")
        workspace = Workspace(str(uuid4()), clean_name)
        with self.repo._lock, self.repo._connect() as conn:
            conn.execute("INSERT INTO workspaces(id, name) VALUES (?,?)", (workspace.id, workspace.name))
            conn.execute(
                "INSERT INTO memberships(workspace_id, user_id, role) VALUES (?,?,?)",
                (workspace.id, user.id, "owner"),
            )
        return workspace

    def workspaces(self, token: str) -> tuple[tuple[Workspace, str], ...]:
        user = self.user_for_token(token)
        with self.repo._lock, self.repo._connect() as conn:
            rows = conn.execute(
                """
                SELECT w.id, w.name, m.role FROM memberships m
                JOIN workspaces w ON w.id = m.workspace_id
                WHERE m.user_id = ?
                """,
                (user.id,),
            ).fetchall()
        return tuple((Workspace(row["id"], row["name"]), row["role"]) for row in rows)

    def principal(self, token: str, workspace_id: str) -> Principal:
        user = self.user_for_token(token)
        with self.repo._lock, self.repo._connect() as conn:
            row = conn.execute(
                "SELECT role FROM memberships WHERE workspace_id = ? AND user_id = ?",
                (workspace_id, user.id),
            ).fetchone()
        if not row:
            raise ForbiddenError("workspace membership required")
        role = row["role"]
        inherited = {"publisher", "auditor"} if role == "owner" else set()
        return Principal(user.id, workspace_id, frozenset({role, *inherited}))

    def add_member(self, token: str, workspace_id: str, email: str, role: str) -> None:
        actor = self.principal(token, workspace_id)
        if "owner" not in actor.roles:
            raise ForbiddenError("owner role required")
        if role not in self.ROLES:
            raise ValueError("invalid role")
        with self.repo._lock, self.repo._connect() as conn:
            user = conn.execute("SELECT id FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
            if not user:
                raise ValueError("user not found")
            conn.execute(
                """
                INSERT INTO memberships(workspace_id, user_id, role) VALUES (?,?,?)
                ON CONFLICT(workspace_id, user_id) DO UPDATE SET role = excluded.role
                """,
                (workspace_id, user["id"], role),
            )


def build_runtime() -> tuple[Any, AuthProvider]:
    """Select durable storage from environment. Production refuses in-memory."""
    env = os.getenv("TRADEPILOT_ENV", "development").lower()
    db_url = os.getenv("DATABASE_URL", "").strip()
    db_path = os.getenv("TRADEPILOT_DB_PATH", "").strip()

    if db_url.startswith("postgresql://") or db_url.startswith("postgres://"):
        try:
            from .postgres_store import PostgresAuthProvider, PostgresRepository
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg is required for Postgres DATABASE_URL") from exc
        repo = PostgresRepository(db_url)
        return repo, PostgresAuthProvider(repo)

    if db_path or db_url.startswith("sqlite"):
        path = db_path or db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not path:
            path = "data/tradepilot.sqlite3"
        repo = SqliteRepository(path)
        return repo, SqliteAuthProvider(repo)

    if env == "production":
        raise RuntimeError("production requires DATABASE_URL or TRADEPILOT_DB_PATH")

    from .auth import InMemoryAuthProvider
    from .core import InMemoryRepository

    return InMemoryRepository(), InMemoryAuthProvider()
