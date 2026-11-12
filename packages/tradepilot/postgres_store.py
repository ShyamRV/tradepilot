from __future__ import annotations

import hashlib
import hmac
import json
import pickle
import secrets
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .auth import AuthenticationError, User, Workspace
from .core import AuditEvent, ForbiddenError, OutboxMessage, Principal

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError as exc:  # pragma: no cover
    raise ImportError("Install psycopg[binary] for Postgres support") from exc


# Mirrors migrations/0002_app_runtime.sql (without outer transaction wrapper).
RUNTIME_DDL = """
CREATE TABLE IF NOT EXISTS app_users (
  id text PRIMARY KEY,
  email text NOT NULL,
  salt bytea NOT NULL,
  password_hash bytea NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT app_users_email_normalized CHECK (email = lower(btrim(email))),
  CONSTRAINT app_users_email_unique UNIQUE (email)
);
CREATE TABLE IF NOT EXISTS auth_sessions (
  token_hash text PRIMARY KEY,
  user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS app_workspaces (
  id text PRIMARY KEY,
  name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS app_memberships (
  workspace_id text NOT NULL REFERENCES app_workspaces(id) ON DELETE CASCADE,
  user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('owner', 'publisher', 'auditor', 'member')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);
CREATE TABLE IF NOT EXISTS app_documents (
  bucket text NOT NULL,
  tenant_id text NOT NULL,
  doc_key text NOT NULL,
  value bytea NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (bucket, tenant_id, doc_key)
);
CREATE TABLE IF NOT EXISTS app_audit_events (
  id text PRIMARY KEY,
  tenant_id text NOT NULL,
  actor_id text NOT NULL,
  action text NOT NULL,
  resource text NOT NULL,
  occurred_at timestamptz NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS app_outbox (
  id text PRIMARY KEY,
  tenant_id text NOT NULL,
  topic text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL,
  sent boolean NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS app_workspace_controls (
  workspace_id text PRIMARY KEY REFERENCES app_workspaces(id) ON DELETE CASCADE,
  quotas jsonb NOT NULL DEFAULT '{}'::jsonb,
  feature_flags jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS app_outbox_pending_idx ON app_outbox (created_at) WHERE sent = false;
CREATE INDEX IF NOT EXISTS app_audit_tenant_time_idx ON app_audit_events (tenant_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS app_documents_tenant_bucket_idx ON app_documents (tenant_id, bucket);
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PostgresRepository:
    """Postgres-backed repository using additive app_* runtime tables."""

    def __init__(self, database_url: str, *, apply_schema: bool = True) -> None:
        self.database_url = database_url
        if apply_schema:
            self._init_schema()

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(RUNTIME_DDL)
            conn.commit()

    def ping(self) -> bool:
        with self._connect() as conn:
            conn.execute("SELECT 1")
        return True

    def append_audit(self, event: AuditEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO app_audit_events(id, tenant_id, actor_id, action, resource, occurred_at, detail)
                VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    event.id,
                    event.tenant_id,
                    event.actor_id,
                    event.action,
                    event.resource,
                    event.occurred_at,
                    json.dumps(event.detail),
                ),
            )
            conn.commit()

    def audits(self, tenant_id: str) -> tuple[AuditEvent, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM app_audit_events WHERE tenant_id = %s ORDER BY occurred_at",
                (tenant_id,),
            ).fetchall()
        return tuple(
            AuditEvent(
                id=row["id"],
                tenant_id=row["tenant_id"],
                actor_id=row["actor_id"],
                action=row["action"],
                resource=row["resource"],
                occurred_at=row["occurred_at"],
                detail=row["detail"] if isinstance(row["detail"], dict) else json.loads(row["detail"]),
            )
            for row in rows
        )

    def put(self, bucket: str, tenant_id: str, key: str, value: Any) -> bool:
        payload = pickle.dumps(value, protocol=4)
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO app_documents(bucket, tenant_id, doc_key, value)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (bucket, tenant_id, key, payload),
                )
                conn.commit()
                return True
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return False

    def replace(self, bucket: str, tenant_id: str, key: str, value: Any) -> None:
        payload = pickle.dumps(value, protocol=4)
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE app_documents
                SET value = %s, updated_at = now()
                WHERE bucket = %s AND tenant_id = %s AND doc_key = %s
                """,
                (payload, bucket, tenant_id, key),
            )
            if cur.rowcount == 0:
                raise KeyError(key)
            conn.commit()

    def get(self, bucket: str, tenant_id: str, key: str) -> Any | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT value FROM app_documents
                WHERE bucket = %s AND tenant_id = %s AND doc_key = %s
                """,
                (bucket, tenant_id, key),
            ).fetchone()
        return pickle.loads(bytes(row["value"])) if row else None

    def values(self, bucket: str, tenant_id: str) -> tuple[Any, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT value FROM app_documents WHERE bucket = %s AND tenant_id = %s",
                (bucket, tenant_id),
            ).fetchall()
        return tuple(pickle.loads(bytes(row["value"])) for row in rows)

    def delete(self, bucket: str, tenant_id: str, key: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                DELETE FROM app_documents
                WHERE bucket = %s AND tenant_id = %s AND doc_key = %s
                """,
                (bucket, tenant_id, key),
            )
            conn.commit()
            return cur.rowcount > 0

    def enqueue(self, message: OutboxMessage) -> bool:
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO app_outbox(id, tenant_id, topic, payload, created_at, sent)
                    VALUES (%s,%s,%s,%s::jsonb,%s,FALSE)
                    """,
                    (
                        message.id,
                        message.tenant_id,
                        message.topic,
                        json.dumps(message.payload),
                        message.created_at,
                    ),
                )
                conn.commit()
                return True
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return False

    def pending(self) -> tuple[OutboxMessage, ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM app_outbox WHERE sent = FALSE ORDER BY created_at"
            ).fetchall()
        return tuple(
            OutboxMessage(
                id=row["id"],
                tenant_id=row["tenant_id"],
                topic=row["topic"],
                payload=row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"]),
                created_at=row["created_at"],
            )
            for row in rows
        )

    def mark_sent(self, message_id: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE app_outbox SET sent = TRUE WHERE id = %s", (message_id,))
            conn.commit()


class PostgresAuthProvider:
    ROLES = {"owner", "publisher", "auditor", "member"}

    def __init__(self, repository: PostgresRepository) -> None:
        self.repo = repository

    @staticmethod
    def _password_hash(password: str, salt: bytes) -> bytes:
        return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

    @staticmethod
    def _session_key(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def register(self, email: str, password: str) -> User:
        normalized = email.strip().lower()
        if "@" not in normalized or len(password) < 8:
            raise AuthenticationError("valid email and password of at least 8 characters required")
        salt = secrets.token_bytes(16)
        user = User(str(uuid4()), normalized)
        with self.repo._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO app_users(id, email, salt, password_hash) VALUES (%s,%s,%s,%s)",
                    (user.id, normalized, salt, self._password_hash(password, salt)),
                )
                conn.commit()
            except psycopg.errors.UniqueViolation as exc:
                conn.rollback()
                raise AuthenticationError("account already exists") from exc
        return user

    def login(self, email: str, password: str) -> str:
        with self.repo._connect() as conn:
            row = conn.execute(
                "SELECT id, salt, password_hash FROM app_users WHERE email = %s",
                (email.strip().lower(),),
            ).fetchone()
            if not row or not hmac.compare_digest(
                bytes(row["password_hash"]), self._password_hash(password, bytes(row["salt"]))
            ):
                raise AuthenticationError("invalid credentials")
            token = secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO auth_sessions(token_hash, user_id, created_at) VALUES (%s,%s,%s)",
                (self._session_key(token), row["id"], _utcnow()),
            )
            conn.commit()
        return token

    def logout(self, token: str) -> None:
        with self.repo._connect() as conn:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash = %s", (self._session_key(token),))
            conn.commit()

    def user_for_token(self, token: str) -> User:
        with self.repo._connect() as conn:
            row = conn.execute(
                """
                SELECT u.id, u.email FROM auth_sessions s
                JOIN app_users u ON u.id = s.user_id
                WHERE s.token_hash = %s
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
        with self.repo._connect() as conn:
            conn.execute("INSERT INTO app_workspaces(id, name) VALUES (%s,%s)", (workspace.id, workspace.name))
            conn.execute(
                "INSERT INTO app_memberships(workspace_id, user_id, role) VALUES (%s,%s,%s)",
                (workspace.id, user.id, "owner"),
            )
            conn.commit()
        return workspace

    def workspaces(self, token: str) -> tuple[tuple[Workspace, str], ...]:
        user = self.user_for_token(token)
        with self.repo._connect() as conn:
            rows = conn.execute(
                """
                SELECT w.id, w.name, m.role FROM app_memberships m
                JOIN app_workspaces w ON w.id = m.workspace_id
                WHERE m.user_id = %s
                """,
                (user.id,),
            ).fetchall()
        return tuple((Workspace(row["id"], row["name"]), row["role"]) for row in rows)

    def principal(self, token: str, workspace_id: str) -> Principal:
        user = self.user_for_token(token)
        with self.repo._connect() as conn:
            row = conn.execute(
                "SELECT role FROM app_memberships WHERE workspace_id = %s AND user_id = %s",
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
        with self.repo._connect() as conn:
            user = conn.execute("SELECT id FROM app_users WHERE email = %s", (email.strip().lower(),)).fetchone()
            if not user:
                raise ValueError("user not found")
            conn.execute(
                """
                INSERT INTO app_memberships(workspace_id, user_id, role) VALUES (%s,%s,%s)
                ON CONFLICT (workspace_id, user_id) DO UPDATE SET role = EXCLUDED.role
                """,
                (workspace_id, user["id"], role),
            )
            conn.commit()
