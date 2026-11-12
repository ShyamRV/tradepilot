"use client";

import Link from "next/link";
import { BarLineChart, MultiLineChart, Sparkline } from "@/components/Charts";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { money, pct } from "@/lib/format";

export default function OverviewPage() {
  const { data } = useWorkspace();
  if (!data) return null;

  return (
    <div className="stack">
      <p className="pageIntro">
        A research desk for delayed NSE cash equities. Review freshness, strategy pressure, and paper exposure before
        moving into detailed pages.
      </p>

      <section className="kpiStrip" aria-label="Workspace summary">
        <article className="kpi">
          <span>Total equity</span>
          <strong>{money.format(data.portfolio.equity)}</strong>
          <small className="positive">{money.format(data.portfolio.pnl)} all time</small>
        </article>
        <article className="kpi">
          <span>Available cash</span>
          <strong>{money.format(data.portfolio.cash)}</strong>
          <small>{((data.portfolio.cash / Math.max(data.portfolio.equity, 1)) * 100).toFixed(1)}% of equity</small>
        </article>
        <article className="kpi">
          <span>Open positions</span>
          <strong>{data.portfolio.positions.length}</strong>
          <small>Paper portfolio only</small>
        </article>
        <article className="kpi">
          <span>Active strategies</span>
          <strong>{data.strategies.filter((item) => item.enabled).length}</strong>
          <small>{data.workspace.market}</small>
        </article>
      </section>

      <section className="vizGrid">
        <BarLineChart
          title="Volume vs momentum"
          subtitle="Session pressure"
          bars={[18, 24, 21, 33, 28, 41, 36, 48, 39, 52, 44, 57]}
          line={[22, 25, 24, 30, 29, 38, 35, 42, 40, 47, 45, 51]}
          medianAt={58}
        />
        <BarLineChart
          title="Risk heat vs setups"
          subtitle="Desk load"
          bars={[12, 16, 14, 22, 19, 27, 24, 31, 28, 35, 30, 38]}
          line={[14, 17, 16, 21, 20, 26, 25, 29, 28, 33, 31, 36]}
        />
        <MultiLineChart
          title="Equity curve"
          metrics={[
            { label: "Paper equity", value: money.format(data.portfolio.equity), tone: "cyan" },
            { label: "PnL", value: money.format(data.portfolio.pnl), tone: "magenta" }
          ]}
          series={[
            { tone: "cyan", values: [88, 90, 89, 93, 95, 94, 97, 99, 98, 102, 104, 107] },
            { tone: "magenta", values: [80, 82, 84, 83, 86, 88, 87, 91, 93, 92, 96, 98] }
          ]}
        />
        <MultiLineChart
          title="Sessions tracked"
          metrics={[
            { label: "Alerts", value: String(data.notifications.length), tone: "lime" },
            { label: "Demo hit rate", value: `${data.backtest.winRatePct}%`, tone: "amber" }
          ]}
          series={[
            { tone: "lime", values: [20, 24, 22, 28, 31, 29, 34, 37, 35, 40, 42, 45] },
            { tone: "amber", values: [18, 19, 21, 20, 23, 25, 24, 27, 29, 28, 30, 32] }
          ]}
        />
      </section>

      <section className="split">
        <article className="panel">
          <header className="panelHeader">
            <h2>Watchlist pulse</h2>
            <Link className="ghostButton" href="/watchlist">
              Open page
            </Link>
          </header>
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Last</th>
                  <th>Day</th>
                  <th>Pulse</th>
                </tr>
              </thead>
              <tbody>
                {data.watchlist.slice(0, 4).map((item) => (
                  <tr key={item.symbol}>
                    <td>
                      <strong>{item.symbol}</strong>
                    </td>
                    <td>{money.format(item.price)}</td>
                    <td className={item.change >= 0 ? "positive" : "negative"}>{pct(item.change)}</td>
                    <td>
                      <Sparkline
                        tone={item.change >= 0 ? "cyan" : "magenta"}
                        values={item.change >= 0 ? [4, 5, 4, 6, 7, 6, 8, 9] : [9, 8, 8, 7, 6, 7, 5, 4]}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel">
          <header className="panelHeader">
            <h2>Latest signals</h2>
            <span className="pill">{data.notifications.length}</span>
          </header>
          {data.notifications.length === 0 ? (
            <div className="emptyState">
              <strong>No notifications</strong>
              <span>Alerts will appear after analysis runs.</span>
            </div>
          ) : (
            <ul className="notificationList">
              {data.notifications.map((item) => (
                <li key={item.id}>
                  <span className={`dot ${item.level}`} />
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.detail}</p>
                    <small>{item.time}</small>
                  </div>
                  <span className="pill">{item.level}</span>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <p className="pageFooter">TradePilot is a research and simulation tool, not a broker or investment adviser.</p>
    </div>
  );
}
