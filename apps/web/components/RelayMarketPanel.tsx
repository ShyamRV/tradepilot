"use client";

import { TradingChart } from "@/components/TradingChart";
import { useQuoteRelay } from "@/lib/use-quote-relay";

function statusLabel(status: "connecting" | "live" | "demo" | "error") {
  switch (status) {
    case "live":
      return "Relay live";
    case "demo":
      return "Simulated relay";
    case "error":
      return "Relay fallback";
    default:
      return "Connecting";
  }
}

export function RelayMarketPanel() {
  const { quotes, provider, status, symbol, setSymbol, active } = useQuoteRelay("AAPL");
  const basePrice = active?.last ?? 100;

  return (
    <section className="panel liveMarketPanel relayMarketPanel" aria-label="US and crypto relay chart">
      <header className="liveMarketHeader">
        <div className="liveMarketIdentity">
          <p className="eyebrow">US / crypto relay</p>
          <div className="liveMarketTitleRow">
            <h2>{active?.symbol ?? "—"}</h2>
            <span className={`streamState ${status === "live" ? "live" : status === "demo" ? "demo" : "connecting"}`}>
              <i />
              {statusLabel(status)}
            </span>
          </div>
          <p>
            One upstream WebSocket (Finnhub/Alpaca when configured) caches prices on the API and fans them out. Browser
            never receives the provider key. Branded chart uses TradingView Lightweight Charts.
          </p>
        </div>
        <div className="liveMarketQuote">
          <strong>
            {active?.symbol?.includes("USDT") ? "" : "$"}
            {active ? active.last.toLocaleString("en-US", { maximumFractionDigits: 4 }) : "—"}
          </strong>
          <span className={(active?.change_pct ?? 0) >= 0 ? "positive" : "negative"}>
            {(active?.change_pct ?? 0) >= 0 ? "+" : ""}
            {(active?.change_pct ?? 0).toFixed(2)}%
          </span>
          <small>
            Source {active?.source ?? provider} · as of{" "}
            {active
              ? new Date(active.as_of).toLocaleTimeString("en-IN", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                  timeZone: "Asia/Kolkata"
                })
              : "—"}{" "}
            IST
          </small>
        </div>
        <div className="liveMarketControls">
          <label>
            Symbol
            <select
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              aria-label="Select US or crypto symbol from relay"
            >
              {quotes.map((item) => (
                <option key={item.symbol} value={item.symbol}>
                  {item.symbol}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>
      {active ? (
        <TradingChart
          key={active.symbol}
          price={basePrice}
          livePrice={active.last}
          height={340}
          ariaLabel={`${active.symbol} branded lightweight chart from quote relay`}
        />
      ) : (
        <div className="emptyState">Waiting for relay quotes…</div>
      )}
      <p className="chartCaption">
        Not Indian exchange data. Provider connection limits stay on the server. Without FINNHUB_API_KEY /
        ALPACA_API_KEY the API serves a simulator with the same fan-out shape.
      </p>
    </section>
  );
}
