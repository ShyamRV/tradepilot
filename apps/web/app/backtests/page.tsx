"use client";

import { BarLineChart, GhostCurveChart, MultiLineChart } from "@/components/Charts";
import { useWorkspace } from "@/components/WorkspaceProvider";

export default function BacktestsPage() {
  const { data, apiConfigured } = useWorkspace();
  if (!data) return null;

  return (
    <div className="stack">
      <p className="pageIntro">
        Returns below are illustrative demo assumptions for education and product walkthroughs. Fees, next-session fills,
        and delayed data quality all change the path. Past paper performance does not guarantee future results.
      </p>

      <section className="kpiStrip">
        <article className="kpi">
          <span>Illustrative strategy return</span>
          <strong className="positive">+{data.backtest.returnPct}%</strong>
          <small>Demo assumption · not a live result</small>
        </article>
        <article className="kpi">
          <span>Illustrative benchmark</span>
          <strong>+{data.backtest.benchmarkPct}%</strong>
          <small>Reference basket assumption</small>
        </article>
        <article className="kpi">
          <span>Max drawdown (demo)</span>
          <strong className="negative">{data.backtest.maxDrawdownPct}%</strong>
          <small>Peak to trough under assumptions</small>
        </article>
        <article className="kpi">
          <span>Hit rate (demo)</span>
          <strong>{data.backtest.winRatePct}%</strong>
          <small>{data.backtest.trades} assumed historical trades</small>
        </article>
      </section>

      <section className="vizGrid">
        <MultiLineChart
          title="Equity vs benchmark (illustrative)"
          metrics={[
            { label: "Strategy (demo)", value: `+${data.backtest.returnPct}%`, tone: "cyan" },
            { label: "Benchmark (demo)", value: `+${data.backtest.benchmarkPct}%`, tone: "magenta" }
          ]}
          series={[
            { tone: "cyan", values: [10, 12, 15, 14, 18, 22, 21, 26, 29, 28, 33, 38] },
            { tone: "magenta", values: [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22] }
          ]}
        />
        <BarLineChart
          title="Trade distribution (demo)"
          subtitle="Bucketed assumed outcomes"
          bars={[8, 12, 18, 24, 21, 16, 11, 7, 5, 3]}
          line={[10, 13, 17, 20, 19, 16, 13, 10, 8, 6]}
          medianAt={40}
        />
        <GhostCurveChart
          title="Path dispersion (demo)"
          values={[5, 8, 12, 11, 16, 21, 20, 26, 31, 29, 35, 40]}
          ghosts={[
            [4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26],
            [6, 7, 10, 13, 15, 18, 22, 21, 25, 28, 30, 33],
            [3, 5, 7, 9, 11, 13, 15, 19, 21, 23, 27, 29]
          ]}
        />
        <article className="panel">
          <header className="panelHeader">
            <h2>Assumptions</h2>
            <span className="pill warn">ILLUSTRATIVE</span>
          </header>
          <ul className="notes">
            <li>Figures are illustrative demo assumptions, not audited performance claims.</li>
            <li>Next-session open fills only; no same-bar execution.</li>
            <li>Indian cash equity fee approximation included in the engine.</li>
            <li>Delayed / EOD data only; no intraday claims.</li>
            <li>Results are educational and not investment advice.</li>
            {!apiConfigured && <li>API URL unset — showing built-in sample backtest numbers only.</li>}
          </ul>
        </article>
      </section>
    </div>
  );
}
