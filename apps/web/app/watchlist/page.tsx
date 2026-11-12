"use client";

import { Sparkline } from "@/components/Charts";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { pct, price } from "@/lib/format";

export default function WatchlistPage() {
  const { data } = useWorkspace();
  if (!data) return null;

  return (
    <div className="stack">
      <p className="pageIntro">
        Track NSE names with published end-of-day prices only. Sparklines are illustrative momentum shapes for the demo
        desk, not intraday ticks.
      </p>

      <section className="kpiStrip">
        {data.watchlist.slice(0, 4).map((item) => (
          <article className="sparkCard" key={item.symbol}>
            <span>{item.symbol}</span>
            <strong>{price.format(item.price)}</strong>
            <small className={item.change >= 0 ? "positive" : "negative"}>{pct(item.change)}</small>
            <Sparkline
              tone={item.signal === "Candidate" ? "lime" : item.change >= 0 ? "cyan" : "magenta"}
              values={
                item.change >= 0
                  ? [12, 14, 13, 16, 18, 17, 20, 22, 21, 24]
                  : [24, 22, 23, 20, 18, 19, 16, 15, 14, 13]
              }
            />
          </article>
        ))}
      </section>

      <section className="panel">
        <header className="panelHeader">
          <h2>Full watchlist</h2>
          <span className="pill">{data.watchlist.length} symbols</span>
        </header>
        {data.watchlist.length === 0 ? (
          <div className="emptyState">
            <strong>No watchlist prices</strong>
            <span>Add an NSE symbol and publish a dataset to see it here.</span>
          </div>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Last</th>
                  <th>Day</th>
                  <th>Signal</th>
                  <th>Shape</th>
                </tr>
              </thead>
              <tbody>
                {data.watchlist.map((item) => (
                  <tr key={item.symbol}>
                    <td>
                      <strong>{item.symbol}</strong>
                    </td>
                    <td>{price.format(item.price)}</td>
                    <td className={item.change >= 0 ? "positive" : "negative"}>{pct(item.change)}</td>
                    <td>
                      <span className={`pill ${item.signal === "Candidate" ? "good" : ""}`}>{item.signal}</span>
                    </td>
                    <td style={{ minWidth: 120 }}>
                      <Sparkline
                        tone={item.change >= 0 ? "cyan" : "magenta"}
                        values={item.change >= 0 ? [3, 4, 5, 4, 6, 7, 8, 9] : [9, 8, 7, 8, 6, 5, 4, 3]}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
