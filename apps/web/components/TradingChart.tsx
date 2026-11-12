"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  createChart,
  type UTCTimestamp
} from "lightweight-charts";
import { candlesFor } from "@/lib/trading";

export function TradingChart({ price }: { price: number }) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    const chart = createChart(container.current, {
      autoSize: true,
      height: 410,
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#93a0b4" },
      grid: { vertLines: { color: "rgba(148,163,184,.08)" }, horzLines: { color: "rgba(148,163,184,.08)" } },
      rightPriceScale: { borderColor: "rgba(148,163,184,.18)" },
      timeScale: { borderColor: "rgba(148,163,184,.18)", timeVisible: true }
    });
    const data = candlesFor(price);
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#2dd4a7",
      downColor: "#ff6b7a",
      wickUpColor: "#2dd4a7",
      wickDownColor: "#ff6b7a",
      borderVisible: false
    });
    candleSeries.setData(
      data.map((item) => ({
        time: item.time as UTCTimestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close
      }))
    );
    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: ""
    });
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    volume.setData(
      data.map((item) => ({
        time: item.time as UTCTimestamp,
        value: item.volume,
        color: item.close >= item.open ? "rgba(45,212,167,.35)" : "rgba(255,107,122,.35)"
      }))
    );
    chart.timeScale().fitContent();
    const observer = new ResizeObserver(() => chart.timeScale().fitContent());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [price]);

  return <div ref={container} className="tradingChart" aria-label="Five minute candlestick and volume chart" />;
}
