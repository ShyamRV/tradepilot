from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkspaceRecord:
    workspace_id: Mapped[str] = mapped_column(String(128), index=True)


class BrokerConnection(Base, WorkspaceRecord):
    __tablename__ = "execution_broker_connections"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    provider: Mapped[str] = mapped_column(String(64))
    environment: Mapped[str] = mapped_column(String(16), default="sandbox")
    account_ref: Mapped[str] = mapped_column(String(256))
    secret_ref: Mapped[str] = mapped_column(String(512))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class OrderIntent(Base, WorkspaceRecord):
    __tablename__ = "execution_order_intents"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    agent_id: Mapped[str | None] = mapped_column(String(128))
    symbol: Mapped[str] = mapped_column(String(32))
    exchange: Mapped[str] = mapped_column(String(8), default="NSE")
    side: Mapped[str] = mapped_column(String(8))
    order_type: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[int] = mapped_column(Integer)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(30, 12))
    status: Mapped[str] = mapped_column(String(32))
    authority_version: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_execution_intent_workspace_id"),
        Index("ix_execution_intents_workspace_status", "workspace_id", "status"),
    )


class RiskDecisionRecord(Base, WorkspaceRecord):
    __tablename__ = "execution_risk_decisions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_intent_id: Mapped[str] = mapped_column(
        ForeignKey("execution_order_intents.id", ondelete="RESTRICT"), index=True
    )
    allowed: Mapped[bool] = mapped_column(Boolean)
    checks: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    quote_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    formula_version: Mapped[str] = mapped_column(String(64))
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class BrokerOrder(Base, WorkspaceRecord):
    __tablename__ = "execution_broker_orders"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_intent_id: Mapped[str] = mapped_column(
        ForeignKey("execution_order_intents.id", ondelete="RESTRICT"), unique=True
    )
    provider_order_id: Mapped[str | None] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32))
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExecutionEvent(Base, WorkspaceRecord):
    __tablename__ = "execution_events"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    order_intent_id: Mapped[str] = mapped_column(
        ForeignKey("execution_order_intents.id", ondelete="RESTRICT"), index=True
    )
    sequence: Mapped[int] = mapped_column(BigInteger)
    event_type: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(32))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("order_intent_id", "sequence", name="uq_execution_event_sequence"),
    )


class FillRecord(Base, WorkspaceRecord):
    __tablename__ = "execution_fills"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    broker_order_id: Mapped[str] = mapped_column(
        ForeignKey("execution_broker_orders.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(30, 12))
    fees: Mapped[Decimal] = mapped_column(Numeric(30, 12))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PositionRecord(Base, WorkspaceRecord):
    __tablename__ = "execution_positions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32))
    quantity: Mapped[int] = mapped_column(Integer)
    average_price: Mapped[Decimal] = mapped_column(Numeric(30, 12))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(30, 12))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("workspace_id", "symbol", name="uq_execution_position_symbol"),
    )


class ExecutionControl(Base, WorkspaceRecord):
    __tablename__ = "execution_controls"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    scope: Mapped[str] = mapped_column(String(32))
    scope_ref: Mapped[str] = mapped_column(String(128), default="global")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("workspace_id", "scope", "scope_ref", name="uq_execution_control_scope"),
    )


class AgentDefinition(Base, WorkspaceRecord):
    __tablename__ = "execution_agents"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32))
    strategy: Mapped[str] = mapped_column(String(120))
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    authority_version: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AgentDecisionRecord(Base, WorkspaceRecord):
    __tablename__ = "execution_agent_decisions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("execution_agents.id", ondelete="RESTRICT"), index=True
    )
    signal: Mapped[dict[str, Any]] = mapped_column(JSON)
    rationale: Mapped[dict[str, Any]] = mapped_column(JSON)
    risk_decision_id: Mapped[str | None] = mapped_column(
        ForeignKey("execution_risk_decisions.id", ondelete="RESTRICT")
    )
    order_intent_id: Mapped[str | None] = mapped_column(
        ForeignKey("execution_order_intents.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
