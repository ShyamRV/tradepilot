from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4

from .core import Repository


class AgentStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    KILLED = "killed"


AGENT_TRANSITIONS = {
    AgentStatus.CREATED: {"start": AgentStatus.RUNNING, "kill": AgentStatus.KILLED},
    AgentStatus.RUNNING: {
        "pause": AgentStatus.PAUSED,
        "stop": AgentStatus.STOPPED,
        "kill": AgentStatus.KILLED,
    },
    AgentStatus.PAUSED: {
        "resume": AgentStatus.RUNNING,
        "stop": AgentStatus.STOPPED,
        "kill": AgentStatus.KILLED,
    },
    AgentStatus.STOPPED: {"start": AgentStatus.RUNNING, "kill": AgentStatus.KILLED},
}


@dataclass(frozen=True)
class AgentConfig:
    name: str
    symbols: tuple[str, ...]
    strategy: str
    max_capital: Decimal
    max_daily_loss: Decimal

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.strategy.strip() or not self.symbols:
            raise ValueError("agent name, strategy and symbols are required")
        if self.max_capital <= 0 or self.max_daily_loss <= 0 or self.max_daily_loss > self.max_capital:
            raise ValueError("invalid agent capital limits")


@dataclass(frozen=True)
class TradingAgent:
    id: str
    workspace_id: str
    config: AgentConfig
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_control_reason: str | None = None

    def control(self, action: str, reason: str) -> "TradingAgent":
        if not reason.strip():
            raise ValueError("control reason required")
        target = AGENT_TRANSITIONS.get(self.status, {}).get(action)
        if target is None:
            raise ValueError(f"invalid agent transition: {self.status} via {action}")
        return replace(
            self,
            status=target,
            updated_at=datetime.now(timezone.utc),
            last_control_reason=reason.strip(),
        )


class AgentControlPlane:
    BUCKET = "autonomous_agents"

    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def create(self, workspace_id: str, config: AgentConfig) -> TradingAgent:
        agent = TradingAgent(str(uuid4()), workspace_id, config)
        self.repository.put(self.BUCKET, workspace_id, agent.id, agent)
        return agent

    def get(self, workspace_id: str, agent_id: str) -> TradingAgent | None:
        return self.repository.get(self.BUCKET, workspace_id, agent_id)

    def list(self, workspace_id: str) -> tuple[TradingAgent, ...]:
        return self.repository.values(self.BUCKET, workspace_id)

    def control(self, workspace_id: str, agent_id: str, action: str, reason: str) -> TradingAgent:
        agent = self.get(workspace_id, agent_id)
        if agent is None:
            raise KeyError(agent_id)
        changed = agent.control(action, reason)
        self.repository.replace(self.BUCKET, workspace_id, agent_id, changed)
        return changed
