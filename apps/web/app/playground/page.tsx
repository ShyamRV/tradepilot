"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import {
  AGENT_PIPELINE_DEMO,
  PLAYGROUND_STEPS,
  isPlaygroundComplete,
  playgroundProgress,
  type PlaygroundStepId
} from "@/lib/playground";
import { usePlaygroundStore } from "@/lib/playground-store";
import { instruments } from "@/lib/trading";
import { useTradingStore } from "@/lib/trading-store";
import { money } from "@/lib/format";

export default function PlaygroundPage() {
  const { data } = useWorkspace();
  const placeOrder = useTradingStore((state) => state.placeOrder);
  const setAgentStatus = useTradingStore((state) => state.setAgentStatus);
  const agents = useTradingStore((state) => state.agents);
  const {
    completed,
    sampleOrderId,
    controlsAcknowledged,
    liveInterest,
    completeStep,
    setSampleOrderId,
    acknowledgeControls,
    expressLiveInterest,
    reset
  } = usePlaygroundStore();

  const [pipelineIndex, setPipelineIndex] = useState(0);
  const [tradeBusy, setTradeBusy] = useState(false);
  const [tradeMessage, setTradeMessage] = useState<string | null>(null);

  const progress = playgroundProgress(completed);
  const done = isPlaygroundComplete(completed);
  const demoAgent = agents[0];
  const sample = instruments[0];
  const cash = data?.portfolio.cash ?? 1_000_000;

  const checklist = useMemo(
    () =>
      PLAYGROUND_STEPS.map((step) => ({
        ...step,
        done: completed.includes(step.id)
      })),
    [completed]
  );

  function mark(id: PlaygroundStepId) {
    completeStep(id);
  }

  function submitSampleTrade() {
    setTradeBusy(true);
    setTradeMessage(null);
    try {
      const order = placeOrder({
        exchange: sample.exchange,
        symbol: sample.symbol,
        side: "BUY",
        type: "MARKET",
        quantity: 1,
        product: "CNC",
        price: sample.price
      });
      setSampleOrderId(order.id);
      mark("sample-trade");
      setTradeMessage(
        `Paper fill recorded for 1 × ${sample.symbol} at ~₹${sample.price.toLocaleString("en-IN")}. Ticket ${order.id.slice(0, 8)}.`
      );
    } catch (reason) {
      setTradeMessage(reason instanceof Error ? reason.message : "Unable to place sample order.");
    } finally {
      setTradeBusy(false);
    }
  }

  function advancePipeline() {
    const next = Math.min(pipelineIndex + 1, AGENT_PIPELINE_DEMO.length - 1);
    setPipelineIndex(next);
    if (next === AGENT_PIPELINE_DEMO.length - 1) {
      mark("agent-walkthrough");
    }
  }

  function playgroundKill() {
    if (demoAgent && demoAgent.status !== "KILLED") {
      setAgentStatus(demoAgent.id, "PAUSED");
    }
    acknowledgeControls();
  }

  return (
    <div className="stack playgroundPage">
      <header className="sectionHero">
        <div>
          <p className="eyebrow">Learn with dummy capital</p>
          <h2>Playground</h2>
          <p>
            Trade with simulated money, run AI agents in a sandbox, and build trust in the controls before any live
            broker link is offered. Performance here is educational only — not a prediction of real results.
          </p>
        </div>
        <div className="playgroundProgressCard" aria-label="Playground progress">
          <span>Progress</span>
          <strong>{progress}%</strong>
          <div className="playgroundMeter" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <i style={{ width: `${progress}%` }} />
          </div>
          <small>{done ? "Playground path complete" : `${completed.length} of ${PLAYGROUND_STEPS.length} steps`}</small>
        </div>
      </header>

      <div className="disclosure">
        This entire section uses paper / dummy trading only. Live execution stays unreachable until a separate audited
        feature flag and your explicit confirmation. Automated agents can still amplify simulated losses — use Pause and
        Kill while you learn.
      </div>

      <section className="playgroundLayout">
        <ol className="playgroundChecklist" aria-label="Playground steps">
          {checklist.map((step, index) => (
            <li key={step.id} className={step.done ? "done" : undefined}>
              <span className="playgroundStepIndex" aria-hidden="true">
                {step.done ? "✓" : index + 1}
              </span>
              <div>
                <strong>{step.title}</strong>
                <p>{step.blurb}</p>
              </div>
            </li>
          ))}
        </ol>

        <div className="playgroundPanels">
          <article className="panel" id="paper-capital">
            <header className="panelHeader">
              <h2>1 · Dummy capital</h2>
              <span className={`pill ${completed.includes("paper-capital") ? "good" : "warn"}`}>
                {completed.includes("paper-capital") ? "Done" : "Start here"}
              </span>
            </header>
            <p className="playgroundLead">
              Your workspace cash is simulated. Use it to learn order tickets and agent limits without funding a broker.
            </p>
            <dl className="metricGrid">
              <div>
                <span>Paper cash</span>
                <strong>{money.format(cash)}</strong>
              </div>
              <div>
                <span>Mode</span>
                <strong>Sandbox</strong>
              </div>
            </dl>
            <button
              type="button"
              className="primary"
              onClick={() => mark("paper-capital")}
              disabled={completed.includes("paper-capital")}
            >
              {completed.includes("paper-capital") ? "Understood" : "I understand — this is not real money"}
            </button>
          </article>

          <article className="panel" id="sample-trade">
            <header className="panelHeader">
              <h2>2 · Sample trade</h2>
              <span className={`pill ${completed.includes("sample-trade") ? "good" : ""}`}>
                {completed.includes("sample-trade") ? "Filled" : "Guided"}
              </span>
            </header>
            <p className="playgroundLead">
              Place a one-share market buy on {sample.symbol}. Same ticket flow as the terminal — paper fill only.
            </p>
            <div className="playgroundTradePreview">
              <div>
                <span>Instrument</span>
                <strong>
                  {sample.exchange}:{sample.symbol}
                </strong>
              </div>
              <div>
                <span>Side · qty</span>
                <strong>BUY · 1 CNC</strong>
              </div>
              <div>
                <span>Est. price</span>
                <strong>₹{sample.price.toLocaleString("en-IN")}</strong>
              </div>
            </div>
            <div className="formActions">
              <button type="button" className="primary" disabled={tradeBusy} onClick={submitSampleTrade}>
                {tradeBusy ? "Submitting…" : completed.includes("sample-trade") ? "Place another sample" : "Submit sample paper order"}
              </button>
              <Link className="ghostButton inlineButton" href={`/terminal/${sample.exchange}/${sample.symbol}`}>
                Open full terminal
              </Link>
            </div>
            {tradeMessage && <p className="playgroundNote">{tradeMessage}</p>}
            {sampleOrderId && (
              <p className="playgroundNote muted">
                Last sample ticket: <code>{sampleOrderId.slice(0, 8)}</code> — also listed under Portfolio / Terminal history.
              </p>
            )}
          </article>

          <article className="panel" id="agent-walkthrough">
            <header className="panelHeader">
              <h2>3 · AI agent decision walkthrough</h2>
              <span className="pill">{AGENT_PIPELINE_DEMO[pipelineIndex].stage}</span>
            </header>
            <p className="playgroundLead">
              Agents do not “promise” returns. Every delegated trade must pass an explainable pipeline before a sandbox
              order is risked.
            </p>
            <ol className="pipelineStages" aria-label="Agent pipeline stages">
              {AGENT_PIPELINE_DEMO.map((item, index) => (
                <li key={item.stage} className={index === pipelineIndex ? "active" : index < pipelineIndex ? "passed" : undefined}>
                  <button type="button" onClick={() => setPipelineIndex(index)}>
                    {item.title}
                  </button>
                </li>
              ))}
            </ol>
            <div className="pipelineDetail" aria-live="polite">
              <h3>{AGENT_PIPELINE_DEMO[pipelineIndex].title}</h3>
              <p>{AGENT_PIPELINE_DEMO[pipelineIndex].detail}</p>
            </div>
            <div className="formActions">
              <button
                type="button"
                className="primary"
                onClick={advancePipeline}
                disabled={pipelineIndex >= AGENT_PIPELINE_DEMO.length - 1 && completed.includes("agent-walkthrough")}
              >
                {pipelineIndex >= AGENT_PIPELINE_DEMO.length - 1 ? "Walkthrough complete" : "Next stage"}
              </button>
              <Link className="ghostButton inlineButton" href="/agents/new">
                Create your own agent
              </Link>
              {demoAgent && (
                <Link className="ghostButton inlineButton" href={`/agents/${demoAgent.id}`}>
                  Open demo control room
                </Link>
              )}
            </div>
          </article>

          <article className="panel" id="controls">
            <header className="panelHeader">
              <h2>4 · Pause &amp; Kill</h2>
              <span className={`pill ${controlsAcknowledged ? "good" : "warn"}`}>
                {controlsAcknowledged ? "Acknowledged" : "Required"}
              </span>
            </header>
            <p className="playgroundLead">
              Trust comes from control. Pause freezes new decisions; Kill permanently blocks that agent from trading
              again. Daily-loss limits auto-pause when breached.
            </p>
            <ul className="notes">
              <li>Start only after you set capital and max daily loss you can tolerate in simulation.</li>
              <li>Review the decision journal before you leave an agent RUNNING overnight.</li>
              <li>Kill cannot reverse fills that already happened — same as a real desk.</li>
            </ul>
            <div className="formActions">
              <button type="button" className="dangerButton" onClick={playgroundKill}>
                {controlsAcknowledged ? "Controls confirmed" : "Try Pause on demo agent"}
              </button>
              <Link className="ghostButton inlineButton" href="/agents">
                Agent list
              </Link>
            </div>
          </article>

          <article className="panel" id="trust-gate">
            <header className="panelHeader">
              <h2>5 · Path to real trading</h2>
              <span className="pill warn">Live gated</span>
            </header>
            <p className="playgroundLead">
              When you are ready, live broker linking will require an audited feature flag plus your explicit
              confirmation. Finish the playground first so you know the agent loop, disclosures, and kill path.
            </p>
            <ul className="trustChecks">
              <li className={completed.includes("paper-capital") ? "on" : undefined}>Dummy capital understood</li>
              <li className={completed.includes("sample-trade") ? "on" : undefined}>Sample paper order placed</li>
              <li className={completed.includes("agent-walkthrough") ? "on" : undefined}>Agent pipeline reviewed</li>
              <li className={completed.includes("controls") ? "on" : undefined}>Pause / Kill confirmed</li>
            </ul>
            <div className="formActions">
              <button
                type="button"
                className="primary"
                disabled={
                  completed.includes("trust-gate") ||
                  !(
                    completed.includes("paper-capital") &&
                    completed.includes("sample-trade") &&
                    completed.includes("agent-walkthrough") &&
                    completed.includes("controls")
                  )
                }
                onClick={() => {
                  mark("trust-gate");
                  expressLiveInterest();
                }}
              >
                {liveInterest || completed.includes("trust-gate")
                  ? "Interest noted — live linking still gated"
                  : "Mark playground complete"}
              </button>
              <button type="button" className="ghostButton" onClick={reset}>
                Reset playground progress
              </button>
            </div>
            {(liveInterest || completed.includes("trust-gate")) && (
              <p className="playgroundNote">
                We recorded that you finished the dummy path. Real trading is not enabled in this release; continue on
                paper until broker linking ships with per-user confirmation.
              </p>
            )}
          </article>
        </div>
      </section>
    </div>
  );
}
