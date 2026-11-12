"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { use, useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { controlBackendAgent, listAgentDecisions, listBackendAgents } from "@/lib/trading-api";
import { useTradingStore } from "@/lib/trading-store";

export default function AgentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const localAgent = useTradingStore((state) => state.agents.find((item) => item.id === id));
  const setLocalStatus = useTradingStore((state) => state.setAgentStatus);
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const queryClient = useQueryClient();
  const backend = useQuery({
    queryKey: ["agents", workspaceId],
    queryFn: () => listBackendAgents({ token, workspaceId }),
    enabled: apiConfigured && Boolean(token && workspaceId)
  });
  const backendAgent = backend.data?.find((item) => item.id === id);
  const decisionQuery = useQuery({
    queryKey: ["agent-decisions", workspaceId, id],
    queryFn: () => listAgentDecisions({ token, workspaceId }, id),
    enabled: apiConfigured && Boolean(token && workspaceId && backendAgent)
  });
  const agent = backendAgent
    ? {
        id: backendAgent.id,
        name: backendAgent.config.name,
        strategy: backendAgent.config.strategy,
        universe: backendAgent.config.symbols.join(", "),
        risk: "Policy",
        capital: backendAgent.config.max_capital,
        dailyLoss: backendAgent.config.max_daily_loss,
        status: backendAgent.status.toUpperCase() as "RUNNING" | "PAUSED" | "KILLED" | "CREATED" | "STOPPED",
        pnl: 0,
        decisions: (decisionQuery.data ?? []).map((decision) => ({
          time: new Date(decision.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
          signal: String(decision.signal.symbol ?? "Strategy evaluation"),
          rationale: String(decision.rationale.summary ?? "Deterministic decision trace"),
          checks: decision.risk_checks.map((check) => String(check.code ?? "check")).join(", "),
          result: decision.resulting_order_id ? `Sandbox order ${decision.resulting_order_id.slice(0, 8)}` : "No order"
        }))
      }
    : localAgent;
  const [confirmKill, setConfirmKill] = useState(false);
  const [controlError, setControlError] = useState("");

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
          `Operator requested ${action} from terminal`
        );
        await queryClient.invalidateQueries({ queryKey: ["agents", workspaceId] });
      } catch (reason) {
        setControlError(reason instanceof Error ? reason.message : "Agent control failed.");
      }
    } else {
      setLocalStatus(agent.id, status);
    }
  }
  if (!agent) return <div className="emptyState"><strong>Agent not found</strong><Link href="/agents">Return to agents</Link></div>;

  return (
    <div className="stack">
      <header className="agentDetailHeader">
        <div><Link href="/agents" className="backLink">← All agents</Link><div className="agentTitle"><h2>{agent.name}</h2><span className={`agentStatus ${agent.status.toLowerCase()}`}><i />{agent.status}</span></div><p>{agent.strategy} on {agent.universe} · {agent.risk} risk</p></div>
        <div className="agentControls">
          {agent.status !== "KILLED" && <button className="ghostButton" onClick={() => void setStatus(agent.status === "RUNNING" ? "PAUSED" : "RUNNING")}>{agent.status === "RUNNING" ? "Pause agent" : "Start agent"}</button>}
          {agent.status !== "KILLED" && <button className="dangerButton" onClick={() => setConfirmKill(true)}>Kill agent</button>}
        </div>
      </header>
      <div className="disclosure">Simulated performance only. Returns exclude real-world execution differences and do not predict future results.</div>
      {controlError && <div className="errorState" role="alert">{controlError} Automation remains fail-closed.</div>}
      <section className="kpiStrip">
        <article className="kpi"><span>Paper P&L</span><strong className={agent.pnl >= 0 ? "positive" : "negative"}>{agent.pnl >= 0 ? "+" : ""}₹{agent.pnl.toLocaleString("en-IN")}</strong><small>Illustrative · not a return promise</small></article>
        <article className="kpi"><span>Allocated capital</span><strong>₹{agent.capital.toLocaleString("en-IN")}</strong><small>Paper account maximum</small></article>
        <article className="kpi"><span>Daily loss stop</span><strong>₹{agent.dailyLoss.toLocaleString("en-IN")}</strong><small>Blocks new simulated orders</small></article>
        <article className="kpi"><span>Decisions</span><strong>{agent.decisions.length}</strong><small>Append-only explanations</small></article>
      </section>
      <section className="split">
        <div className="panel">
          <header className="panelHeader"><h2>Decision journal</h2><span className="pill">Explainable</span></header>
          {agent.decisions.length ? <ol className="decisionList">{agent.decisions.map((decision, index) => <li key={index}><time>{decision.time}</time><div><strong>{decision.signal}</strong><p>{decision.rationale}</p><span>Risk checks · {decision.checks}</span><b>{decision.result}</b></div></li>)}</ol> : <div className="emptyState">No decisions yet. Start the agent to begin simulated evaluation.</div>}
        </div>
        <aside className="panel">
          <header className="panelHeader"><h2>Mandate</h2></header>
          <dl className="metaList"><div><dt>Strategy</dt><dd>{agent.strategy}</dd></div><div><dt>Universe</dt><dd>{agent.universe}</dd></div><div><dt>Risk profile</dt><dd>{agent.risk}</dd></div><div><dt>Execution</dt><dd>Paper only</dd></div></dl>
        </aside>
      </section>
      {confirmKill && <div className="modalBackdrop"><section className="confirmModal" role="alertdialog" aria-modal="true"><h2>Kill {agent.name}?</h2><p>This permanently prevents new decisions and paper orders. Completed activity remains in the audit journal.</p><div className="modalActions"><button className="ghostButton" onClick={() => setConfirmKill(false)}>Keep agent</button><button className="dangerButton" onClick={() => { void setStatus("KILLED"); setConfirmKill(false); }}>Kill permanently</button></div></section></div>}
    </div>
  );
}
