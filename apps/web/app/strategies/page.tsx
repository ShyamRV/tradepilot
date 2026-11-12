"use client";

import { GhostCurveChart } from "@/components/Charts";
import { useWorkspace } from "@/components/WorkspaceProvider";

export default function StrategiesPage() {
  const { data } = useWorkspace();
  if (!data) return null;

  return (
    <div className="stack">
      <p className="pageIntro">
        Strategies are versioned rule templates. The engine evaluates deterministic conditions; the model only explains
        already computed evidence.
      </p>

      <section className="split">
        <article className="panel">
          <header className="panelHeader">
            <h2>Configured templates</h2>
            <span className="pill">{data.strategies.length}</span>
          </header>
          {data.strategies.length === 0 ? (
            <div className="emptyState">
              <strong>No configured strategies</strong>
              <span>Create a strategy through the API to analyse an NSE dataset.</span>
            </div>
          ) : (
            <div className="strategyGrid">
              {data.strategies.map((strategy) => (
                <article className="strategyCard" key={strategy.id}>
                  <div className="strategyTop">
                    <div>
                      <h3>{strategy.name}</h3>
                      <p>{strategy.description || "Workspace strategy"}</p>
                    </div>
                    <span className={`pill ${strategy.enabled ? "good" : ""}`}>
                      {strategy.enabled ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="configRow">
                    <span>Configuration</span>
                    <strong>{strategy.settings || "Stored API specification"}</strong>
                  </div>
                </article>
              ))}
            </div>
          )}
        </article>

        <GhostCurveChart
          title="Rule sensitivity"
          values={[10, 14, 18, 17, 22, 28, 27, 33, 38, 36, 42, 47]}
          ghosts={[
            [8, 11, 13, 15, 18, 20, 22, 24, 26, 28, 29, 31],
            [12, 13, 16, 19, 21, 25, 24, 29, 31, 34, 35, 39],
            [6, 9, 12, 14, 16, 19, 23, 22, 27, 30, 33, 34]
          ]}
        />
      </section>
    </div>
  );
}
