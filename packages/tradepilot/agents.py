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


class AgentHorizon(StrEnum):
    INTRADAY = "intraday"
    SWING = "swing"
    POSITION = "position"


class AutonomyMode(StrEnum):
    DELEGATED = "delegated"  # after Start, paper loop may submit through risk gates
    ADVISORY = "advisory"  # decide and journal only; no orders


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
    horizon: AgentHorizon = AgentHorizon.INTRADAY
    setups: tuple[str, ...] = ()
    stop_rule: str = "or_mid"
    target_r: Decimal = Decimal("1")
    autonomy_mode: AutonomyMode = AutonomyMode.DELEGATED
    flat_by_minute: int | None = 235  # minutes from session open; ~15:55 on 9:30 open

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.strategy.strip() or not self.symbols:
            raise ValueError("agent name, strategy and symbols are required")
        if self.max_capital <= 0 or self.max_daily_loss <= 0 or self.max_daily_loss > self.max_capital:
            raise ValueError("invalid agent capital limits")
        if self.target_r <= 0:
            raise ValueError("target_r must be positive")
        if self.horizon == AgentHorizon.INTRADAY and self.flat_by_minute is not None and self.flat_by_minute <= 0:
            raise ValueError("flat_by_minute must be positive for intraday agents")


@dataclass(frozen=True)
class TradingAgent:
    id: str
    workspace_id: str
    config: AgentConfig
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_control_reason: str | None = None
    daily_pnl: Decimal = Decimal("0")
    last_pipeline_stage: str | None = None

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

    def replace(self, workspace_id: str, agent: TradingAgent) -> TradingAgent:
        self.repository.replace(self.BUCKET, workspace_id, agent.id, agent)
        return agent

    def control(self, workspace_id: str, agent_id: str, action: str, reason: str) -> TradingAgent:
        agent = self.get(workspace_id, agent_id)
        if agent is None:
            raise KeyError(agent_id)
        changed = agent.control(action, reason)
        return self.replace(workspace_id, changed)
