"use client";

import { MultiLineChart } from "@/components/Charts";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { money } from "@/lib/format";

export default function AnalysisPage() {
  const { data } = useWorkspace();
  if (!data) return null;

  const passed = data.analysis.rules.filter((rule) => rule.result === "pass").length;
  const failed = data.analysis.rules.filter((rule) => rule.result === "fail").length;
  const total = data.analysis.rules.length;

  return (
    <div className="stack">
      <p className="pageIntro">
        Every rule below is backed by recorded indicator inputs. Counts show how many rules passed or failed — not a
        probability of profit or expected return.
      </p>

      <section className="split">
        <article className="panel">
          <header className="panelHeader">
            <h2>Analysis evidence{data.analysis.symbol ? ` · ${data.analysis.symbol}` : ""}</h2>
            <span className={`pill ${passed > 0 ? "good" : ""}`}>{data.analysis.verdict || "No signal"}</span>
          </header>

          <div className="metricGrid" style={{ marginBottom: 16 }}>
            <div>
              <span>Rules passed</span>
              <strong className="positive">
                {passed}
                {total > 0 ? ` / ${total}` : ""}
              </strong>
            </div>
            <div>
              <span>Rules failed</span>
              <strong className={failed > 0 ? "negative" : ""}>{failed}</strong>
            </div>
            <div>
              <span>Decision</span>
              <strong className={data.risk.decision === "Allowed" ? "positive" : "negative"}>{data.risk.decision}</strong>
            </div>
          </div>

          {data.analysis.rules.length === 0 ? (
            <div className="emptyState">
              <strong>No analysis evidence</strong>
              <span>Run an analysis after publishing a dataset and strategy.</span>
            </div>
          ) : (
            <ul className="ruleList">
              {data.analysis.rules.map((rule) => (
                <li key={rule.label}>
                  <span className={`ruleIcon ${rule.result}`}>{rule.result === "pass" ? "✓" : "×"}</span>
                  <div>
                    <strong>{rule.label}</strong>
                    <p>{rule.evidence}</p>
                  </div>
                  <span className={`pill ${rule.result === "pass" ? "good" : "bad"}`}>{rule.result}</span>
                </li>
              ))}
            </ul>
          )}
        </article>

        <div className="stack">
          <article className="panel">
            <header className="panelHeader">
              <h2>Risk result</h2>
              <span className={`pill ${data.risk.decision === "Allowed" ? "good" : "bad"}`}>{data.risk.decision}</span>
            </header>
            <div className="riskNumbers">
              <div>
                <span>Max position</span>
                <strong>{money.format(data.risk.maxPosition)}</strong>
              </div>
              <div>
                <span>Risk per trade</span>
                <strong>{money.format(data.risk.riskPerTrade)}</strong>
              </div>
            </div>
            <ul className="notes">
              {data.risk.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
            <button type="button" className="primary">
              Review paper order
            </button>
          </article>

          <MultiLineChart
            title="Indicator path"
            metrics={[
              { label: "EMA spread", value: "8.4%", tone: "cyan" },
              { label: "Volume x", value: "1.34", tone: "magenta" }
            ]}
            series={[
              { tone: "cyan", values: [20, 22, 25, 24, 28, 31, 30, 34, 38, 37, 41, 45] },
              { tone: "magenta", values: [18, 19, 21, 23, 22, 26, 29, 28, 32, 35, 34, 38] }
            ]}
          />
        </div>
      </section>

      <article className="panel">
        <header className="panelHeader">
          <h2>Data notes</h2>
        </header>
        <dl className="metaList">
          <div>
            <dt>Source</dt>
            <dd>{data.metadata.source}</dd>
          </div>
          <div>
            <dt>As of</dt>
            <dd>{data.metadata.asOf}</dd>
          </div>
          <div>
            <dt>Adjustment</dt>
            <dd>{data.metadata.adjustment}</dd>
          </div>
          <div>
            <dt>Limitations</dt>
            <dd>{data.metadata.limitations}</dd>
          </div>
        </dl>
      </article>
    </div>
  );
}
