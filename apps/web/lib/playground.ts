export const PLAYGROUND_STEPS = [
  {
    id: "paper-capital",
    title: "Understand dummy capital",
    blurb: "Your desk starts with simulated cash. Nothing here moves real money."
  },
  {
    id: "sample-trade",
    title: "Place a sample trade",
    blurb: "Submit a paper market order and see how fills, product type, and tickets work."
  },
  {
    id: "agent-walkthrough",
    title: "Watch an AI agent decide",
    blurb: "Step through scan → entry → exit → size → risk → sandbox order with full rationale."
  },
  {
    id: "controls",
    title: "Try Pause and Kill",
    blurb: "Confirm you can stop an agent instantly and that daily-loss limits freeze new risk."
  },
  {
    id: "trust-gate",
    title: "Trust checklist before live",
    blurb: "Live broker linking stays gated. Finish the playground so you know what you are delegating."
  }
] as const;

export type PlaygroundStepId = (typeof PLAYGROUND_STEPS)[number]["id"];

export const AGENT_PIPELINE_DEMO = [
  {
    stage: "scan",
    title: "Scan",
    detail: "Opening-range breakout flagged on RELIANCE after volume expansion above the 15-minute OR high."
  },
  {
    stage: "entry",
    title: "Entry",
    detail: "Long trigger at breakout retest. Stop anchored to OR mid. Target set at 1R."
  },
  {
    stage: "exit",
    title: "Exit plan",
    detail: "Hard stop, profit target, and flat-by 15:25 IST for intraday horizon."
  },
  {
    stage: "budget",
    title: "Size",
    detail: "Position sized so a stop-out stays under the agent’s max daily loss."
  },
  {
    stage: "timemachine",
    title: "Odds panel",
    detail: "Historical similar setups show win rate and expectancy for education — not a forecast."
  },
  {
    stage: "risk",
    title: "Risk gate",
    detail: "Liquidity, exposure, and daily-loss checks passed. Reject path would stop here with an audit row."
  },
  {
    stage: "execute",
    title: "Sandbox order",
    detail: "Paper BUY submitted through BrokerGateway sandbox with slippage and partial-fill simulation."
  }
] as const;

export function playgroundProgress(completed: PlaygroundStepId[]): number {
  const total = PLAYGROUND_STEPS.length;
  const unique = new Set(completed);
  const done = PLAYGROUND_STEPS.filter((step) => unique.has(step.id)).length;
  return Math.round((done / total) * 100);
}

export function isPlaygroundComplete(completed: PlaygroundStepId[]): boolean {
  return PLAYGROUND_STEPS.every((step) => completed.includes(step.id));
}
