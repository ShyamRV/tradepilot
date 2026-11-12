from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .ports.llm import LLMProvider


@dataclass(frozen=True)
class AgentDecision:
    id: str
    agent_id: str
    signal: Mapping[str, Any]
    indicators: tuple[Mapping[str, Any], ...]
    rationale: Mapping[str, Any]
    risk_checks: tuple[Mapping[str, Any], ...]
    authority_version: str
    resulting_order_id: str | None
    created_at: datetime


class AgentRuntime(Protocol):
    """Coordinates typed decisions; it has no BrokerGateway capability."""

    def decide(
        self,
        *,
        agent_id: str,
        signal: Mapping[str, Any],
        indicators: tuple[Mapping[str, Any], ...],
        risk_checks: tuple[Mapping[str, Any], ...],
        authority_version: str,
        resulting_order_id: str | None = None,
    ) -> AgentDecision: ...


class DeterministicAgentRuntime:
    """Safe local runtime and fallback for a future Fetch.ai uAgents adapter."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    def decide(
        self,
        *,
        agent_id: str,
        signal: Mapping[str, Any],
        indicators: tuple[Mapping[str, Any], ...],
        risk_checks: tuple[Mapping[str, Any], ...],
        authority_version: str,
        resulting_order_id: str | None = None,
    ) -> AgentDecision:
        evidence = {
            "signal": dict(signal),
            "indicators": [dict(item) for item in indicators],
            "risk_checks": [dict(item) for item in risk_checks],
        }
        rationale: Mapping[str, Any] = (
            self.llm.explain(evidence)
            if self.llm is not None
            else {
                "summary": "Deterministic fallback; no model was invoked.",
                "model_version": "deterministic-fallback-v1",
            }
        )
        return AgentDecision(
            id=str(uuid4()),
            agent_id=agent_id,
            signal=dict(signal),
            indicators=indicators,
            rationale=dict(rationale),
            risk_checks=risk_checks,
            authority_version=authority_version,
            resulting_order_id=resulting_order_id,
            created_at=datetime.now(timezone.utc),
        )
