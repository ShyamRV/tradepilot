"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { agentSchema } from "@/lib/trading";
import { createBackendAgent } from "@/lib/trading-api";
import { useTradingStore } from "@/lib/trading-store";

export default function NewAgentPage() {
  const router = useRouter();
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const createAgent = useTradingStore((state) => state.createAgent);
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function submit(formData: FormData) {
    const parsed = agentSchema.safeParse(Object.fromEntries(formData));
    if (!parsed.success) {
      setErrors(Object.fromEntries(parsed.error.issues.map((issue) => [String(issue.path[0]), issue.message])));
      return;
    }
    try {
      if (apiConfigured && token && workspaceId) {
        const backend = await createBackendAgent(
          { token, workspaceId },
          {
            name: parsed.data.name,
            symbols: parsed.data.universe.split(",").map((value) => value.trim().toUpperCase()).filter(Boolean),
            strategy: parsed.data.strategy,
            max_capital: String(parsed.data.capital),
            max_daily_loss: String(parsed.data.dailyLoss)
          }
        );
        router.push(`/agents/${backend.id}`);
      } else {
        const agent = createAgent(parsed.data);
        await Promise.resolve();
        router.push(`/agents/${agent.id}`);
      }
    } catch (reason) {
      setErrors({ form: reason instanceof Error ? reason.message : "Unable to create agent." });
    }
  }

  return (
    <div className="agentBuilder">
      <header className="sectionHero"><div><p className="eyebrow">Guardrails first</p><h2>Create an AI agent</h2><p>Configure a paper-trading mandate. New agents begin paused so you can review every setting.</p></div></header>
      <form
        className="panel formGrid"
        action="#"
        method="post"
        onSubmit={(event) => {
          event.preventDefault();
          event.stopPropagation();
          void submit(new FormData(event.currentTarget));
        }}
      >
        {errors.form && <div className="fieldError full" role="alert">{errors.form}</div>}
        <label className="full">Agent name<input name="name" placeholder="e.g. Quality Momentum" aria-invalid={Boolean(errors.name)} />{errors.name && <span>{errors.name}</span>}</label>
        <label>Strategy<select name="strategy"><option>Momentum</option><option>Mean reversion</option><option>Breakout</option></select></label>
        <label>Risk profile<select name="risk"><option>Conservative</option><option>Balanced</option><option>Aggressive</option></select></label>
        <label className="full">Trading universe<input name="universe" placeholder="NIFTY 50 or comma-separated symbols" />{errors.universe && <span>{errors.universe}</span>}</label>
        <label>Maximum capital (₹)<input name="capital" type="number" min="1" defaultValue="250000" />{errors.capital && <span>{errors.capital}</span>}</label>
        <label>Maximum daily loss (₹)<input name="dailyLoss" type="number" min="1" defaultValue="5000" />{errors.dailyLoss && <span>{errors.dailyLoss}</span>}</label>
        <div className="riskNotice full"><strong>Paper execution only.</strong> No strategy guarantees returns. The daily-loss control pauses new decisions after simulated losses cross the configured threshold.</div>
        <div className="formActions full"><button type="button" className="ghostButton" onClick={() => router.back()}>Cancel</button><button className="primary" type="submit">Create paused agent</button></div>
      </form>
    </div>
  );
}
