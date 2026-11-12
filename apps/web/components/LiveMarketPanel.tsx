"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { TradingChart } from "@/components/TradingChart";
import { instruments } from "@/lib/trading";
import { useMarketStream } from "@/lib/use-market-stream";

const nseInstruments = instruments.filter((item) => item.exchange === "NSE");

function statusLabel(status: "connecting" | "live" | "demo" | "stale") {
  switch (status) {
    case "live":
      return "Live stream";
    case "demo":
      return "Simulated live";
    case "stale":
      return "Stream stale";
    default:
      return "Connecting";
  }
}

export function LiveMarketPanel() {
  const [symbol, setSymbol] = useState<string>(nseInstruments[0]?.symbol ?? "RELIANCE");
  const instrument = useMemo(
    () => nseInstruments.find((item) => item.symbol === symbol) ?? nseInstruments[0],
    [symbol]
  );
  const { tick, status } = useMarketStream(instrument.exchange, instrument.symbol, instrument.price);
  const asOf = new Date(tick.asOf).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Kolkata"
  });

  return (
    <section className="panel liveMarketPanel" aria-label="Live market graph">
      <header className="liveMarketHeader">
        <div className="liveMarketIdentity">
          <p className="eyebrow">Market graph</p>
          <div className="liveMarketTitleRow">
            <h2>{instrument.symbol}</h2>
            <span className="exchangeTag">{instrument.exchange}</span>
            <span className={`streamState ${status}`}>
              <i />
              {statusLabel(status)}
            </span>
          </div>
          <p>{instrument.name}</p>
        </div>
        <div className="liveMarketQuote">
          <strong>₹{tick.price.toFixed(2)}</strong>
          <span className={tick.change >= 0 ? "positive" : "negative"}>
            {tick.change >= 0 ? "+" : ""}
            {tick.change.toFixed(2)}%
          </span>
          <small>As of {asOf} IST · {tick.source === "stream" ? "API feed" : "paper simulator"}</small>
        </div>
        <div className="liveMarketControls">
          <label>
            Symbol
            <select
              value={instrument.symbol}
              onChange={(event) => setSymbol(event.target.value)}
              aria-label="Select instrument for live graph"
            >
              {nseInstruments.map((item) => (
                <option key={item.symbol} value={item.symbol}>
                  {item.symbol}
                </option>
              ))}
            </select>
          </label>
          <Link className="ghostButton" href={`/terminal/${instrument.exchange}/${instrument.symbol}`}>
            Open terminal
          </Link>
        </div>
      </header>
      <TradingChart
        price={instrument.price}
        livePrice={tick.price}
        height={360}
        ariaLabel={`${instrument.symbol} live five minute candlestick and volume chart`}
      />
      <p className="chartCaption">
        Candles update from the live tick stream. Without a licensed NSE realtime feed this desk uses the sandbox
        simulator or API quote socket — not exchange-entitled live prices.
      </p>
    </section>
  );
}
