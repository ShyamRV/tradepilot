from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4


class ForbiddenError(PermissionError):
    pass


@dataclass(frozen=True)
class Principal:
    user_id: str
    workspace_id: str
    roles: frozenset[str] = frozenset()


def authorize(principal: Principal, workspace_id: str, required_role: str | None = None) -> None:
    if principal.workspace_id != workspace_id:
        raise ForbiddenError("cross-workspace access denied")
    if required_role and required_role not in principal.roles:
        raise ForbiddenError(f"role {required_role!r} required")


@dataclass(frozen=True)
class AuditEvent:
    id: str
    tenant_id: str
    actor_id: str
    action: str
    resource: str
    occurred_at: datetime
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OutboxMessage:
    id: str
    tenant_id: str
    topic: str
    payload: dict[str, Any]
    created_at: datetime


class Repository(Protocol):
    def append_audit(self, event: AuditEvent) -> None: ...
    def audits(self, tenant_id: str) -> tuple[AuditEvent, ...]: ...
    def put(self, bucket: str, tenant_id: str, key: str, value: Any) -> bool: ...
    def replace(self, bucket: str, tenant_id: str, key: str, value: Any) -> None: ...
    def get(self, bucket: str, tenant_id: str, key: str) -> Any | None: ...
    def values(self, bucket: str, tenant_id: str) -> tuple[Any, ...]: ...
    def delete(self, bucket: str, tenant_id: str, key: str) -> bool: ...
    def enqueue(self, message: OutboxMessage) -> bool: ...
    def pending(self) -> tuple[OutboxMessage, ...]: ...
    def mark_sent(self, message_id: str) -> None: ...


class PostgresRepository(Protocol):
    """Persistence port; production adapters implement transactions and tenant RLS."""

    def transaction(self) -> Any: ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str, str], Any] = {}
        self._audit: list[AuditEvent] = []
        self._outbox: dict[str, OutboxMessage] = {}
        self._sent: set[str] = set()

    def append_audit(self, event: AuditEvent) -> None:
        self._audit.append(event)

    def audits(self, tenant_id: str) -> tuple[AuditEvent, ...]:
        return tuple(e for e in self._audit if e.tenant_id == tenant_id)

    def put(self, bucket: str, tenant_id: str, key: str, value: Any) -> bool:
        storage_key = (bucket, tenant_id, key)
        if storage_key in self._data:
            return False
        self._data[storage_key] = value
        return True

    def replace(self, bucket: str, tenant_id: str, key: str, value: Any) -> None:
        storage_key = (bucket, tenant_id, key)
        if storage_key not in self._data:
            raise KeyError(key)
        self._data[storage_key] = value

    def get(self, bucket: str, tenant_id: str, key: str) -> Any | None:
        return self._data.get((bucket, tenant_id, key))

    def values(self, bucket: str, tenant_id: str) -> tuple[Any, ...]:
        return tuple(v for (b, t, _), v in self._data.items() if b == bucket and t == tenant_id)

    def delete(self, bucket: str, tenant_id: str, key: str) -> bool:
        return self._data.pop((bucket, tenant_id, key), None) is not None

    def enqueue(self, message: OutboxMessage) -> bool:
        if message.id in self._outbox:
            return False
        self._outbox[message.id] = message
        return True

    def pending(self) -> tuple[OutboxMessage, ...]:
        return tuple(m for key, m in self._outbox.items() if key not in self._sent)

    def mark_sent(self, message_id: str) -> None:
        self._sent.add(message_id)

    def ping(self) -> bool:
        return True


def audit(repo: Repository, principal: Principal, action: str, resource: str, **detail: Any) -> AuditEvent:
    event = AuditEvent(
        id=str(uuid4()), tenant_id=principal.workspace_id, actor_id=principal.user_id,
        action=action, resource=resource, occurred_at=datetime.now(timezone.utc), detail=detail,
    )
    repo.append_audit(event)
    return event
