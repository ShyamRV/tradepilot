"use client";

import { useMemo, useState } from "react";
import { useTheme } from "@/components/ThemeProvider";
import { TradingViewWidget } from "@/components/tradingview/TradingViewWidget";

const INDEX_SYMBOLS = [
  { s: "NSE:NIFTY", d: "Nifty 50" },
  { s: "NSE:BANKNIFTY", d: "Bank Nifty" },
  { s: "BSE:SENSEX", d: "Sensex" },
  { s: "NSE:INDIAVIX", d: "India VIX" },
  { s: "NSE:NIFTYJR", d: "Nifty Next 50" }
] as const;

const WATCHLIST_SYMBOLS = [
  "NSE:RELIANCE",
  "NSE:TCS",
  "NSE:INFY",
  "NSE:HDFCBANK",
  "NSE:ICICIBANK",
  "NSE:SBIN",
  "NSE:ITC",
  "NSE:BHARTIARTL",
  "NSE:NIFTY",
  "BSE:SENSEX"
] as const;

const CHART_OPTIONS = [
  { value: "NSE:NIFTY", label: "Nifty 50" },
  { value: "NSE:BANKNIFTY", label: "Bank Nifty" },
  { value: "BSE:SENSEX", label: "Sensex" },
  { value: "NSE:RELIANCE", label: "Reliance" },
  { value: "NSE:TCS", label: "TCS" },
  { value: "NSE:INFY", label: "Infosys" },
  { value: "NSE:HDFCBANK", label: "HDFC Bank" }
] as const;

export function IndiaMarketWidgets() {
  const { theme } = useTheme();
  const colorTheme = theme === "dark" ? "dark" : "light";
  const [chartSymbol, setChartSymbol] = useState<string>("NSE:NIFTY");

  const overviewConfig = useMemo(
    () => ({
      colorTheme,
      dateRange: "12M",
      showChart: true,
      locale: "en",
      largeChartUrl: "",
      isTransparent: true,
      showSymbolLogo: true,
      showFloatingTooltip: true,
      width: "100%",
      height: "100%",
      tabs: [
        {
          title: "India indices",
          symbols: INDEX_SYMBOLS.map((item) => ({ s: item.s, d: item.d }))
        }
      ]
    }),
    [colorTheme]
  );

  const watchlistConfig = useMemo(
    () => ({
      width: "100%",
      height: "100%",
      symbolsGroups: [
        {
          name: "NSE / BSE",
          symbols: WATCHLIST_SYMBOLS.map((symbol) => ({
            name: symbol,
            displayName: symbol.replace(/^NSE:|^BSE:/, "")
          }))
        }
      ],
      showSymbolLogo: true,
      isTransparent: true,
      colorTheme,
      locale: "en"
    }),
    [colorTheme]
  );

  const chartConfig = useMemo(
    () => ({
      autosize: true,
      symbol: chartSymbol,
      interval: "15",
      timezone: "Asia/Kolkata",
      theme: colorTheme,
      style: "1",
      locale: "en",
      toolbar_bg: colorTheme === "dark" ? "#0b1220" : "#ffffff",
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_legend: false,
      allow_symbol_change: true,
      calendar: false,
      support_host: "https://www.tradingview.com",
      container_id: `tv_advanced_${chartSymbol.replace(":", "_")}`
    }),
    [chartSymbol, colorTheme]
  );

  return (
    <div className="indiaMarketStack">
      <div className="delayBanner" role="status">
        <strong>15-min delayed</strong>
        <span>
          Indian indices, watchlist, and advanced chart below use TradingView embeds. Quotes are delayed — not live
          exchange ticks, not redistributed NSE/BSE feeds, and not investment advice.
        </span>
      </div>

      <div className="indiaWidgetGrid">
        <TradingViewWidget
          title="Indian indices"
          height={440}
          scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js"
          config={overviewConfig}
        />
        <TradingViewWidget
          title="NSE watchlist"
          height={440}
          scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-market-quotes.js"
          config={watchlistConfig}
        />
      </div>

      <div className="advancedChartShell">
        <div className="advancedChartToolbar">
          <label>
            Advanced chart symbol
            <select
              value={chartSymbol}
              onChange={(event) => setChartSymbol(event.target.value)}
              aria-label="Select symbol for TradingView advanced chart"
            >
              {CHART_OPTIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <span className="delayBadge">15-min delayed</span>
        </div>
        <TradingViewWidget
          title="Advanced chart"
          height={560}
          className="advancedChartWidget"
          scriptSrc="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"
          config={chartConfig}
        />
      </div>
    </div>
  );
}
