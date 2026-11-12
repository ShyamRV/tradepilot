"use client";

import { PortfolioAnalytics } from "@/components/PortfolioAnalytics";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { money, price } from "@/lib/format";

export default function PortfolioPage() {
  const { data } = useWorkspace();
  if (!data) return null;

  return (
    <div className="stack">
      <p className="pageIntro">
        Paper fills use a next-session open model. This page never places broker orders and never holds customer funds.
      </p>

      <section className="kpiStrip">
        <article className="kpi">
          <span>Equity</span>
          <strong>{money.format(data.portfolio.equity)}</strong>
          <small className="positive">{money.format(data.portfolio.pnl)} simulated</small>
        </article>
        <article className="kpi">
          <span>Cash</span>
          <strong>{money.format(data.portfolio.cash)}</strong>
          <small>Available for paper entries</small>
        </article>
        <article className="kpi">
          <span>Positions</span>
          <strong>{data.portfolio.positions.length}</strong>
          <small>Open simulated lots</small>
        </article>
        <article className="kpi">
          <span>Orders</span>
          <strong>{data.history.length}</strong>
          <small>Fill history</small>
        </article>
      </section>

      <PortfolioAnalytics />

      <section className="panel">
        <header className="panelHeader">
          <h2>Open positions</h2>
          <span className="pill">Simulated</span>
        </header>
        {data.portfolio.positions.length === 0 ? (
          <div className="emptyState">
            <strong>No open paper positions</strong>
            <span>Filled paper orders will be reflected here.</span>
          </div>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Average</th>
                  <th>Last</th>
                  <th>Unrealized</th>
                </tr>
              </thead>
              <tbody>
                {data.portfolio.positions.map((position) => {
                  const unrealized = (position.last - position.average) * position.quantity;
                  return (
                    <tr key={position.symbol}>
                      <td>
                        <strong>{position.symbol}</strong>
                      </td>
                      <td>{position.quantity}</td>
                      <td>{price.format(position.average)}</td>
                      <td>{price.format(position.last)}</td>
                      <td className={unrealized >= 0 ? "positive" : "negative"}>{money.format(unrealized)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <header className="panelHeader">
          <h2>Order history</h2>
        </header>
        {data.history.length === 0 ? (
          <div className="emptyState">
            <span>No paper orders recorded.</span>
          </div>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.history.map((trade, index) => (
                  <tr key={`${trade.date}-${trade.symbol}-${index}`}>
                    <td>{trade.date}</td>
                    <td>
                      <strong>{trade.symbol}</strong>
                    </td>
                    <td>{trade.side}</td>
                    <td>{trade.quantity}</td>
                    <td>{price.format(trade.price)}</td>
                    <td>
                      <span className="pill good">{trade.status}</span>
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
