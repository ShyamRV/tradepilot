"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { use, useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import {
  controlBackendAgent,
  listAgentDecisions,
  listBackendAgents,
  tickBackendAgents
} from "@/lib/trading-api";
import { useTradingStore } from "@/lib/trading-store";

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const localAgent = useTradingStore((state) => state.agents.find((item) => item.id === id));
  const setLocalStatus = useTradingStore((state) => state.setAgentStatus);
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const queryClient = useQueryClient();
  const [confirmKill, setConfirmKill] = useState(false);
  const [controlError, setControlError] = useState("");
  const [tickBusy, setTickBusy] = useState(false);
  const [lastTick, setLastTick] = useState<string>("");

  const backend = useQuery({
    queryKey: ["agents", workspaceId],
    queryFn: () => listBackendAgents({ token, workspaceId }),
    enabled: apiConfigured && Boolean(token && workspaceId),
    refetchInterval: 8_000
  });
  const backendAgent = backend.data?.find((item) => item.id === id);
  const decisionQuery = useQuery({
    queryKey: ["agent-decisions", workspaceId, id],
    queryFn: () => listAgentDecisions({ token, workspaceId }, id),
    enabled: apiConfigured && Boolean(token && workspaceId && backendAgent),
    refetchInterval: backendAgent?.status === "running" ? 8_000 : false
  });

  const latestOdds = decisionQuery.data
    ?.map((decision) => decision.rationale?.odds)
    .filter(Boolean)
    .at(-1) as
    | { target_first_pct?: string; stop_first_pct?: string; neither_pct?: string; verdict?: string; seed?: number }
    | undefined;

  const agent = backendAgent
    ? {
        id: backendAgent.id,
        name: backendAgent.config.name,
        strategy: backendAgent.config.strategy,
        universe: backendAgent.config.symbols.join(", "),
        risk: backendAgent.config.autonomy_mode ?? "delegated",
        capital: Number(backendAgent.config.max_capital),
        dailyLoss: Number(backendAgent.config.max_daily_loss),
        status: backendAgent.status.toUpperCase() as "RUNNING" | "PAUSED" | "KILLED" | "CREATED" | "STOPPED",
        pnl: Number(backendAgent.daily_pnl ?? 0),
        horizon: backendAgent.config.horizon ?? "intraday",
        stage: backendAgent.last_pipeline_stage ?? "idle",
        targetR: backendAgent.config.target_r ?? 1,
        stopRule: backendAgent.config.stop_rule ?? "or_mid",
        decisions: (decisionQuery.data ?? []).map((decision) => ({
          time: new Date(decision.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
          signal: `${String(decision.signal.action ?? "eval")} · ${String(decision.signal.symbol ?? "")}`,
          rationale: String(decision.rationale.summary ?? "Deterministic decision trace"),
          checks: decision.risk_checks.map((check) => String(check.code ?? "check")).join(", "),
          result: decision.resulting_order_id
            ? `Sandbox order ${decision.resulting_order_id.slice(0, 8)}`
            : String(decision.signal.stage ?? "No order")
        }))
      }
    : localAgent
      ? {
          ...localAgent,
          horizon: localAgent.horizon ?? "intraday",
          stage: localAgent.lastStage ?? "idle",
          targetR: localAgent.targetR ?? 1,
          stopRule: localAgent.stopRule ?? "or_mid"
        }
      : null;

  async function setStatus(status: "RUNNING" | "PAUSED" | "KILLED") {
    if (!agent) return;
    setControlError("");
    if (backendAgent && token && workspaceId) {
      const action =
        status === "KILLED"
          ? "kill"
          : status === "PAUSED"
            ? "pause"
            : backendAgent.status === "paused"
              ? "resume"
              : "start";
      try {
        await controlBackendAgent(
          { token, workspaceId },
          backendAgent.id,
          action,
          `Operator requested ${action} from control room`
        );
        await queryClient.invalidateQueries({ queryKey: ["agents", workspaceId] });
      } catch (reason) {
        setControlError(reason instanceof Error ? reason.message : "Agent control failed.");
      }
    } else {
      setLocalStatus(agent.id, status);
    }
  }

  async function runCycle() {
    if (!token || !workspaceId) return;
    setTickBusy(true);
    setControlError("");
    try {
      const result = await tickBackendAgents({ token, workspaceId });
      setLastTick(`${result.results.length} event(s) · ${new Date().toLocaleTimeString("en-IN")}`);
      await queryClient.invalidateQueries({ queryKey: ["agents", workspaceId] });
      await queryClient.invalidateQueries({ queryKey: ["agent-decisions", workspaceId, id] });
    } catch (reason) {
      setControlError(reason instanceof Error ? reason.message : "Tick failed.");
    } finally {
      setTickBusy(false);
    }
  }

  if (!agent) {
    return (
      <div className="emptyState">
        <strong>Agent not found</strong>
        <Link href="/agents">Return to agents</Link>
      </div>
    );
  }

  return (
    <div className="stack">
      <header className="agentDetailHeader">
        <div>
          <Link href="/agents" className="backLink">
            ← All agents
          </Link>
          <div className="agentTitle">
            <h2>{agent.name}</h2>
            <span className={`agentStatus ${agent.status.toLowerCase()}`}>
              <i />
              {agent.status}
            </span>
          </div>
          <p>
            {agent.horizon} · {agent.strategy} on {agent.universe} · {agent.risk}
          </p>
        </div>
        <div className="agentControls">
          {apiConfigured && (
            <button type="button" className="ghostButton" disabled={tickBusy} onClick={() => void runCycle()}>
              {tickBusy ? "Running cycle…" : "Run trading cycle"}
            </button>
          )}
          {agent.status !== "KILLED" && (
            <button
              className="ghostButton"
              onClick={() => void setStatus(agent.status === "RUNNING" ? "PAUSED" : "RUNNING")}
            >
              {agent.status === "RUNNING" ? "Pause agent" : "Start agent"}
            </button>
          )}
          {agent.status !== "KILLED" && (
            <button className="dangerButton" onClick={() => setConfirmKill(true)}>
              Kill agent
            </button>
          )}
        </div>
      </header>

      <div className="disclosure">
        Simulated / paper performance only. Time-machine odds are not predictions. Not investment advice.
      </div>
      {controlError && (
        <div className="errorState" role="alert">
          {controlError} Automation remains fail-closed.
        </div>
      )}
      {lastTick && (
        <p className="pageIntro" role="status">
          Last cycle: {lastTick}
        </p>
      )}

      <ol className="workflowSteps" aria-label="Pipeline stage">
        {["scan", "entry", "ready", "blocked"].map((stage) => (
          <li key={stage} className={agent.stage === stage ? "activeStage" : ""}>
            <strong>{stage}</strong>
            <span>{agent.stage === stage ? "Current" : "Pipeline"}</span>
          </li>
        ))}
      </ol>

      <section className="kpiStrip">
        <article className="kpi">
          <span>Paper P&L</span>
          <strong className={agent.pnl >= 0 ? "positive" : "negative"}>
            {agent.pnl >= 0 ? "+" : ""}₹{agent.pnl.toLocaleString("en-IN")}
          </strong>
          <small>Illustrative · not a return promise</small>
        </article>
        <article className="kpi">
          <span>Allocated capital</span>
          <strong>₹{agent.capital.toLocaleString("en-IN")}</strong>
          <small>Paper account maximum</small>
        </article>
        <article className="kpi">
          <span>Daily loss stop</span>
          <strong>₹{agent.dailyLoss.toLocaleString("en-IN")}</strong>
          <small>Auto-pauses new decisions</small>
        </article>
        <article className="kpi">
          <span>Target / stop</span>
          <strong>
            {agent.targetR}R · {agent.stopRule}
          </strong>
          <small>Exit planner rules</small>
        </article>
      </section>

      {latestOdds && (
        <section className="panel oddsPanel">
          <header className="panelHeader">
            <h2>Time machine odds</h2>
            <span className="pill">Simulation</span>
          </header>
          <div className="oddsGrid">
            <div>
              <span>Target first</span>
              <strong>{latestOdds.target_first_pct ?? "—"}%</strong>
            </div>
            <div>
              <span>Stop first</span>
              <strong>{latestOdds.stop_first_pct ?? "—"}%</strong>
            </div>
            <div>
              <span>Neither</span>
              <strong>{latestOdds.neither_pct ?? "—"}%</strong>
            </div>
            <div>
              <span>Verdict</span>
              <strong>{latestOdds.verdict ?? "—"}</strong>
            </div>
          </div>
          <p className="chartCaption">
            Built from recent bar history (seed {latestOdds.seed ?? 19}). Not a prediction — earnings and news can do
            things history never did.
          </p>
        </section>
      )}

      <section className="split">
        <div className="panel">
          <header className="panelHeader">
            <h2>Decision journal</h2>
            <span className="pill">Explainable</span>
          </header>
          {agent.decisions.length ? (
            <ol className="decisionList">
              {agent.decisions.map((decision, index) => (
                <li key={index}>
                  <time>{decision.time}</time>
                  <div>
                    <strong>{decision.signal}</strong>
                    <p>{decision.rationale}</p>
                    <span>Risk checks · {decision.checks}</span>
                    <b>{decision.result}</b>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className="emptyState">
              No decisions yet. Start the agent, then run a trading cycle (or wait for the worker).
            </div>
          )}
        </div>
        <aside className="panel">
          <header className="panelHeader">
            <h2>Mandate</h2>
          </header>
          <dl className="metaList">
            <div>
              <dt>Horizon</dt>
              <dd>{agent.horizon}</dd>
            </div>
            <div>
              <dt>Strategy</dt>
              <dd>{agent.strategy}</dd>
            </div>
            <div>
              <dt>Universe</dt>
              <dd>{agent.universe}</dd>
            </div>
            <div>
              <dt>Execution</dt>
              <dd>Paper sandbox only</dd>
            </div>
          </dl>
        </aside>
      </section>

      {confirmKill && (
        <div className="modalBackdrop">
          <section className="confirmModal" role="alertdialog" aria-modal="true">
            <h2>Kill {agent.name}?</h2>
            <p>
              This permanently prevents new decisions and paper orders. Completed activity remains in the audit
              journal.
            </p>
            <div className="modalActions">
              <button className="ghostButton" onClick={() => setConfirmKill(false)}>
                Keep agent
              </button>
              <button
                className="dangerButton"
                onClick={() => {
                  void setStatus("KILLED");
                  setConfirmKill(false);
                }}
              >
                Kill permanently
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
