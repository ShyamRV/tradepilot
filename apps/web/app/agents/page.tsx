"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { listBackendAgents } from "@/lib/trading-api";
import { useTradingStore } from "@/lib/trading-store";

export default function AgentsPage() {
  const localAgents = useTradingStore((state) => state.agents);
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const backend = useQuery({
    queryKey: ["agents", workspaceId],
    queryFn: () => listBackendAgents({ token, workspaceId }),
    enabled: apiConfigured && Boolean(token && workspaceId)
  });
  const agents = backend.data?.length
    ? backend.data.map((agent) => ({
        id: agent.id,
        name: agent.config.name,
        strategy: agent.config.strategy,
        risk: "Policy",
        universe: agent.config.symbols.join(", "),
        capital: agent.config.max_capital,
        dailyLoss: agent.config.max_daily_loss,
        status: agent.status.toUpperCase(),
        pnl: 0
      }))
    : localAgents;
  return (
    <div className="stack">
      <header className="sectionHero">
        <div><p className="eyebrow">Automation control centre</p><h2>AI agents</h2><p>Delegate paper-trading decisions within explicit capital and loss limits. Every decision remains reviewable.</p></div>
        <div className="heroActions">
          <Link className="ghostButton inlineButton" href="/playground">Playground first</Link>
          <Link className="primary inlineButton" href="/agents/new">Create agent</Link>
        </div>
      </header>
      <div className="disclosure">Agent performance is simulated and does not predict future results. Automated trading can amplify losses. Kill controls stop future actions but cannot reverse completed paper fills. New to agents? Use the Playground to place dummy trades and walk the decision pipeline before you Start.</div>
      {backend.isError && <div className="errorState">Live agent service is unavailable; showing the local sandbox view.</div>}
      <section className="agentGrid">
        {agents.map((agent) => (
          <Link className="agentCard" href={`/agents/${agent.id}`} key={agent.id}>
            <div className="agentTop"><span className={`agentStatus ${agent.status.toLowerCase()}`}><i />{agent.status}</span><span className={agent.pnl >= 0 ? "positive" : "negative"}>{agent.pnl >= 0 ? "+" : ""}₹{agent.pnl.toLocaleString("en-IN")}</span></div>
            <h3>{agent.name}</h3><p>{agent.strategy} · {agent.universe}</p>
            <dl><div><dt>Risk</dt><dd>{agent.risk}</dd></div><div><dt>Capital</dt><dd>₹{agent.capital.toLocaleString("en-IN")}</dd></div><div><dt>Daily stop</dt><dd>₹{agent.dailyLoss.toLocaleString("en-IN")}</dd></div></dl>
            <span className="cardAction">Open control room →</span>
          </Link>
        ))}
      </section>
    </div>
  );
}
