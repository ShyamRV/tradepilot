"use client";

import { RelayMarketPanel } from "@/components/RelayMarketPanel";
import { IndiaMarketWidgets } from "@/components/tradingview/IndiaMarketWidgets";

export default function MarketsPage() {
  return (
    <div className="stack">
      <p className="pageIntro">
        Indian cash equities and indices via free TradingView embeds (clearly labeled 15-min delayed). US stocks and
        crypto update through a server-side quote relay into branded Lightweight Charts — provider API keys never reach
        the browser.
      </p>
      <IndiaMarketWidgets />
      <RelayMarketPanel />
    </div>
  );
}
