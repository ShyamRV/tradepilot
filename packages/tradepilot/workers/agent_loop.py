from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..agent_runtime import AgentRuntime, DeterministicAgentRuntime
from ..agents import AgentControlPlane, AgentStatus, AutonomyMode, TradingAgent
from ..core import Principal, Repository, audit
from ..ports.market_data import MarketDataProvider
from ..realtime import SandboxBroker
from ..risk import PretradeContext, evaluate_pretrade
from ..settings import TradingSettings
from ..strategies.pipeline import evaluate_symbol
from ..trading import OrderRequest, OrderType, Side


class AgentLoopWorker:
    """Ticks RUNNING agents through the day-trader-style pipeline into sandbox orders."""

    def __init__(
        self,
        repository: Repository,
        *,
        settings: TradingSettings,
        market: MarketDataProvider,
        broker: SandboxBroker,
        agent_control: AgentControlPlane | None = None,
        runtime: AgentRuntime | None = None,
        actor: Principal | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.market = market
        self.broker = broker
        self.agents = agent_control or AgentControlPlane(repository)
        self.runtime = runtime or DeterministicAgentRuntime()
        self.actor = actor or Principal(user_id="system", workspace_id="system", roles=frozenset({"system"}))

    def tick_workspace(self, workspace_id: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for agent in self.agents.list(workspace_id):
            if agent.status != AgentStatus.RUNNING:
                continue
            results.extend(self.tick_agent(workspace_id, agent))
        return results

    def tick_agent(self, workspace_id: str, agent: TradingAgent) -> list[dict[str, Any]]:
        if not self.settings.paper_trading:
            raise RuntimeError("agent loop requires PAPER_TRADING=true")
        if not self.settings.autonomous_trading_enabled:
            return [{"agent_id": agent.id, "skipped": "autonomous_trading_disabled"}]
        if agent.daily_pnl <= -agent.config.max_daily_loss:
            paused = agent.control("pause", "daily loss limit reached")
            self.agents.replace(workspace_id, paused)
            audit(self.repository, self.actor, "agent.paused_daily_loss", agent.id)
            return [{"agent_id": agent.id, "paused": "daily_loss_limit"}]

        outcomes: list[dict[str, Any]] = []
        for symbol in agent.config.symbols:
            quote = self.market.quote(symbol)
            pipeline = evaluate_symbol(
                symbol=symbol,
                horizon=agent.config.horizon.value,
                setups=agent.config.setups,
                max_capital=agent.config.max_capital,
                max_daily_loss=agent.config.max_daily_loss,
                daily_pnl=agent.daily_pnl,
                seed=self.settings.simulator_seed,
                base_price=quote.last,
                stop_rule=agent.config.stop_rule,
                target_r=agent.config.target_r,
            )
            agent = replace(agent, last_pipeline_stage=pipeline.stage, updated_at=datetime.now(timezone.utc))
            self.agents.replace(workspace_id, agent)

            decision = self.runtime.decide(
                agent_id=agent.id,
                signal={
                    "symbol": symbol,
                    "action": pipeline.action,
                    "horizon": agent.config.horizon.value,
                    "stage": pipeline.stage,
                    "source": "strategy-pipeline-v1",
                },
                indicators=pipeline.indicators,
                risk_checks=pipeline.risk_checks,
                authority_version=agent.updated_at.isoformat(),
            )
            rationale = {**pipeline.rationale, **dict(decision.rationale)}
            decision = replace(decision, rationale=rationale)
            self.repository.put("agent_decisions", workspace_id, decision.id, decision)

            outcome: dict[str, Any] = {
                "agent_id": agent.id,
                "symbol": symbol,
                "stage": pipeline.stage,
                "action": pipeline.action,
                "decision_id": decision.id,
                "odds": pipeline.rationale.get("odds"),
                "quantity": pipeline.quantity,
            }
            if pipeline.action != "buy" or pipeline.quantity <= 0 or pipeline.plan is None:
                outcomes.append(outcome)
                continue
            if agent.config.autonomy_mode != AutonomyMode.DELEGATED:
                outcome["skipped"] = "advisory_mode"
                outcomes.append(outcome)
                continue
            if not self.settings.broker_execution_enabled:
                outcome["skipped"] = "broker_execution_disabled"
                outcomes.append(outcome)
                continue

            order_id = str(uuid4())
            request = OrderRequest(
                id=order_id,
                workspace_id=workspace_id,
                symbol=symbol,
                side=Side.BUY,
                quantity=pipeline.quantity,
                order_type=OrderType.MARKET,
                agent_id=agent.id,
            )
            risk = evaluate_pretrade(
                request,
                quote,
                PretradeContext(
                    equity=agent.config.max_capital,
                    cash=agent.config.max_capital,
                    daily_pnl=agent.daily_pnl,
                    current_position=0,
                    open_orders=0,
                ),
            )
            self.repository.put("risk_decisions", workspace_id, order_id, risk)
            if not risk.allowed:
                outcome["rejected"] = list(risk.reasons)
                outcomes.append(outcome)
                continue
            control = self.repository.get("execution_controls", workspace_id, "workspace") or {}
            if control.get("killed") or self.settings.global_execution_kill:
                outcome["rejected"] = ["execution_killed"]
                outcomes.append(outcome)
                continue

            order = self.broker.submit(request, quote)
            self.repository.put("sandbox_orders", workspace_id, order_id, order)
            decision = replace(decision, resulting_order_id=order_id)
            self.repository.replace("agent_decisions", workspace_id, decision.id, decision)
            audit(
                self.repository,
                self.actor,
                "agent.sandbox_order",
                order_id,
                agent_id=agent.id,
                symbol=symbol,
                quantity=pipeline.quantity,
                status=order.status.value,
            )
            outcome["order_id"] = order_id
            outcome["order_status"] = order.status.value
            outcomes.append(outcome)
        return outcomes
