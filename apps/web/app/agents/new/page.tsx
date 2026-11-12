"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { agentSchema } from "@/lib/trading";
import { createBackendAgent } from "@/lib/trading-api";
import { useTradingStore } from "@/lib/trading-store";

const HORIZON_TEMPLATES = {
  intraday: {
    label: "Day trader",
    strategy: "Opening range",
    stopRule: "or_mid",
    targetR: "1",
    blurb: "ORB / flags / oversold bounce. Flat by session end. Same pipeline as day-trader-skill."
  },
  swing: {
    label: "Swing trader",
    strategy: "Swing trend",
    stopRule: "prior_low",
    targetR: "2",
    blurb: "Multi-day MA reclaim and breakouts. Wider stops, higher R targets."
  },
  position: {
    label: "Long-term",
    strategy: "Swing trend",
    stopRule: "pct",
    targetR: "3",
    blurb: "Position-style trend following with conservative sizing and 3R targets."
  }
} as const;

export default function NewAgentPage() {
  const router = useRouter();
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const createAgent = useTradingStore((state) => state.createAgent);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [horizon, setHorizon] = useState<keyof typeof HORIZON_TEMPLATES>("intraday");
  const [capital, setCapital] = useState("250000");
  const [dailyLoss, setDailyLoss] = useState("5000");
  const template = HORIZON_TEMPLATES[horizon];

  const sizingHint = useMemo(() => {
    const maxCapital = Number(capital);
    const maxLoss = Number(dailyLoss);
    if (!Number.isFinite(maxCapital) || !Number.isFinite(maxLoss) || maxCapital <= 0 || maxLoss <= 0) {
      return "Set capital and daily-loss limits before creating the agent.";
    }
    if (maxLoss >= maxCapital) return "Daily loss must stay below allocated capital (risk gate).";
    const pct = ((maxLoss / maxCapital) * 100).toFixed(1);
    return `Budget check: max ₹${maxLoss.toLocaleString("en-IN")} daily loss is ${pct}% of capital. Starts paused — Start delegates autonomous paper trading.`;
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
            max_daily_loss: String(parsed.data.dailyLoss),
            horizon: parsed.data.horizon,
            stop_rule: parsed.data.stopRule,
            target_r: String(parsed.data.targetR),
            autonomy_mode: parsed.data.autonomyMode,
            flat_by_minute: parsed.data.horizon === "intraday" ? 235 : null,
            setups:
              parsed.data.horizon === "intraday"
                ? ["orb", "breakout_20d", "bull_flag", "oversold_bounce"]
                : ["swing_ma50_reclaim", "breakout_20d", "reclaim_ma20"]
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
          <p className="eyebrow">Autonomous paper agents</p>
          <h2>Create an AI agent</h2>
          <p>
            Day-trader and longer-horizon templates run scan → entry → exit → size → time-machine odds → risk → sandbox
            order after you Start. GLM only explains; risk code decides.
          </p>
        </div>
      </header>

      <div className="horizonPicker" role="group" aria-label="Trading horizon">
        {(Object.keys(HORIZON_TEMPLATES) as Array<keyof typeof HORIZON_TEMPLATES>).map((key) => (
          <button
            key={key}
            type="button"
            className={horizon === key ? "active" : ""}
            onClick={() => setHorizon(key)}
          >
            <strong>{HORIZON_TEMPLATES[key].label}</strong>
            <span>{HORIZON_TEMPLATES[key].blurb}</span>
          </button>
        ))}
      </div>

      <ol className="workflowSteps" aria-label="Agent workflow">
        <li>
          <strong>Scan</strong>
          <span>Setups in universe</span>
        </li>
        <li>
          <strong>Entry</strong>
          <span>Bar-close trigger</span>
        </li>
        <li>
          <strong>Budget / risk</strong>
          <span>Size + daily stop</span>
        </li>
        <li>
          <strong>Execute</strong>
          <span>Paper sandbox only</span>
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
        <input type="hidden" name="horizon" value={horizon} />
        <input type="hidden" name="stopRule" value={template.stopRule} />
        <input type="hidden" name="targetR" value={template.targetR} />
        <input type="hidden" name="strategy" value={template.strategy} />
        <label className="full">
          Agent name
          <input name="name" placeholder="e.g. ORB Desk Alpha" aria-invalid={Boolean(errors.name)} />
          {errors.name && <span>{errors.name}</span>}
        </label>
        <label>
          Risk profile
          <select name="risk">
            <option>Conservative</option>
            <option>Balanced</option>
            <option>Aggressive</option>
          </select>
        </label>
        <label>
          Autonomy
          <select name="autonomyMode" defaultValue="delegated">
            <option value="delegated">Delegated (auto paper trades after Start)</option>
            <option value="advisory">Advisory (journal only)</option>
          </select>
        </label>
        <label className="full">
          Trading universe
          <input name="universe" placeholder="RELIANCE,TCS,INFY" defaultValue="RELIANCE,TCS" />
          {errors.universe && <span>{errors.universe}</span>}
        </label>
        <label>
          Maximum capital (₹)
          <input name="capital" type="number" min="1" value={capital} onChange={(e) => setCapital(e.target.value)} />
          {errors.capital && <span>{errors.capital}</span>}
        </label>
        <label>
          Maximum daily loss (₹)
          <input
            name="dailyLoss"
            type="number"
            min="1"
            value={dailyLoss}
            onChange={(e) => setDailyLoss(e.target.value)}
          />
          {errors.dailyLoss && <span>{errors.dailyLoss}</span>}
        </label>
        <div className="riskNotice full">
          <strong>{template.label} · {template.targetR}R · stop {template.stopRule}.</strong> {sizingHint}
        </div>
        <div className="riskNotice full">
          <strong>Paper only.</strong> Not investment advice. Kill stops future actions; completed fills stay in the
          journal.
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
