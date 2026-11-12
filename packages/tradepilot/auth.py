from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .core import ForbiddenError, Principal


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True)
class User:
    id: str
    email: str


@dataclass(frozen=True)
class Workspace:
    id: str
    name: str


class AuthProvider(Protocol):
    """Auth port. Production deployments should inject a managed identity provider."""

    def register(self, email: str, password: str) -> User: ...
    def login(self, email: str, password: str) -> str: ...
    def logout(self, token: str) -> None: ...
    def user_for_token(self, token: str) -> User: ...
    def create_workspace(self, token: str, name: str) -> Workspace: ...
    def workspaces(self, token: str) -> tuple[tuple[Workspace, str], ...]: ...
    def principal(self, token: str, workspace_id: str) -> Principal: ...
    def add_member(self, token: str, workspace_id: str, email: str, role: str) -> None: ...


class InMemoryAuthProvider:
    """Test/dev auth only; sessions are process-local and disappear on restart."""

    ROLES = {"owner", "publisher", "auditor", "member"}

    def __init__(self) -> None:
        self._users: dict[str, tuple[User, bytes, bytes]] = {}
        self._sessions: dict[str, str] = {}
        self._workspaces: dict[str, Workspace] = {}
        self._memberships: dict[tuple[str, str], str] = {}

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
        if normalized in self._users:
            raise AuthenticationError("account already exists")
        salt = secrets.token_bytes(16)
        user = User(str(uuid4()), normalized)
        self._users[normalized] = (user, salt, self._password_hash(password, salt))
        return user

    def login(self, email: str, password: str) -> str:
        record = self._users.get(email.strip().lower())
        if not record or not hmac.compare_digest(record[2], self._password_hash(password, record[1])):
            raise AuthenticationError("invalid credentials")
        token = secrets.token_urlsafe(32)
        self._sessions[self._session_key(token)] = record[0].id
        return token

    def logout(self, token: str) -> None:
        self._sessions.pop(self._session_key(token), None)

    def user_for_token(self, token: str) -> User:
        user_id = self._sessions.get(self._session_key(token))
        if not user_id:
            raise AuthenticationError("invalid or expired session")
        return next(record[0] for record in self._users.values() if record[0].id == user_id)

    def create_workspace(self, token: str, name: str) -> Workspace:
        user = self.user_for_token(token)
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("workspace name required")
        workspace = Workspace(str(uuid4()), clean_name)
        self._workspaces[workspace.id] = workspace
        self._memberships[(workspace.id, user.id)] = "owner"
        return workspace

    def workspaces(self, token: str) -> tuple[tuple[Workspace, str], ...]:
        user = self.user_for_token(token)
        return tuple(
            (self._workspaces[workspace_id], role)
            for (workspace_id, user_id), role in self._memberships.items()
            if user_id == user.id
        )

    def principal(self, token: str, workspace_id: str) -> Principal:
        user = self.user_for_token(token)
        role = self._memberships.get((workspace_id, user.id))
        if not role:
            raise ForbiddenError("workspace membership required")
        inherited = {"publisher", "auditor"} if role == "owner" else set()
        return Principal(user.id, workspace_id, frozenset({role, *inherited}))

    def add_member(self, token: str, workspace_id: str, email: str, role: str) -> None:
        actor = self.principal(token, workspace_id)
        if "owner" not in actor.roles:
            raise ForbiddenError("owner role required")
        if role not in self.ROLES:
            raise ValueError("invalid role")
        record = self._users.get(email.strip().lower())
        if not record:
            raise ValueError("user not found")
        self._memberships[(workspace_id, record[0].id)] = role
