"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { agentSchema } from "@/lib/trading";
import { createBackendAgent } from "@/lib/trading-api";
import { useTradingStore } from "@/lib/trading-store";

export default function NewAgentPage() {
  const router = useRouter();
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const createAgent = useTradingStore((state) => state.createAgent);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [capital, setCapital] = useState("250000");
  const [dailyLoss, setDailyLoss] = useState("5000");

  const sizingHint = useMemo(() => {
    const maxCapital = Number(capital);
    const maxLoss = Number(dailyLoss);
    if (!Number.isFinite(maxCapital) || !Number.isFinite(maxLoss) || maxCapital <= 0 || maxLoss <= 0) {
      return "Set capital and daily-loss limits before creating the agent.";
    }
    if (maxLoss >= maxCapital) {
      return "Daily loss must stay below allocated capital (risk gate).";
    }
    const pct = ((maxLoss / maxCapital) * 100).toFixed(1);
    return `Budget check: max ₹${maxLoss.toLocaleString("en-IN")} daily loss is ${pct}% of ₹${maxCapital.toLocaleString("en-IN")} capital. Agent starts paused — review before Start.`;
  }, [capital, dailyLoss]);

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
      <header className="sectionHero">
        <div>
          <p className="eyebrow">Guardrails first</p>
          <h2>Create an AI agent</h2>
          <p>
            Same discipline as a day-trading desk: size the risk, check limits, then allow execution. New agents begin
            paused so nothing runs until you say start.
          </p>
        </div>
      </header>
      <ol className="workflowSteps" aria-label="Agent workflow">
        <li>
          <strong>Mandate</strong>
          <span>Name, universe, strategy</span>
        </li>
        <li>
          <strong>Budget</strong>
          <span>Capital and max loss per day</span>
        </li>
        <li>
          <strong>Risk gate</strong>
          <span>Daily stop must stay under capital</span>
        </li>
        <li>
          <strong>Paused create</strong>
          <span>You start it from the control room</span>
        </li>
      </ol>
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
        {errors.form && (
          <div className="fieldError full" role="alert">
            {errors.form}
          </div>
        )}
        <label className="full">
          Agent name
          <input name="name" placeholder="e.g. Quality Momentum" aria-invalid={Boolean(errors.name)} />
          {errors.name && <span>{errors.name}</span>}
        </label>
        <label>
          Strategy
          <select name="strategy">
            <option>Momentum</option>
            <option>Mean reversion</option>
            <option>Breakout</option>
          </select>
        </label>
        <label>
          Risk profile
          <select name="risk">
            <option>Conservative</option>
            <option>Balanced</option>
            <option>Aggressive</option>
          </select>
        </label>
        <label className="full">
          Trading universe
          <input name="universe" placeholder="NIFTY 50 or comma-separated symbols" />
          {errors.universe && <span>{errors.universe}</span>}
        </label>
        <label>
          Maximum capital (₹)
          <input
            name="capital"
            type="number"
            min="1"
            value={capital}
            onChange={(event) => setCapital(event.target.value)}
          />
          {errors.capital && <span>{errors.capital}</span>}
        </label>
        <label>
          Maximum daily loss (₹)
          <input
            name="dailyLoss"
            type="number"
            min="1"
            value={dailyLoss}
            onChange={(event) => setDailyLoss(event.target.value)}
          />
          {errors.dailyLoss && <span>{errors.dailyLoss}</span>}
        </label>
        <div className="riskNotice full">
          <strong>Budget / risk check.</strong> {sizingHint}
        </div>
        <div className="riskNotice full">
          <strong>Paper execution only.</strong> No strategy guarantees returns. Kill stops future decisions; it cannot
          reverse completed paper fills.
        </div>
        <div className="formActions full">
          <button type="button" className="ghostButton" onClick={() => router.back()}>
            Cancel
          </button>
          <button className="primary" type="submit">
            Create paused agent
          </button>
        </div>
      </form>
    </div>
  );
}
