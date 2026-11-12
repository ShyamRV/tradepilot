"use client";

import { useEffect, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp
} from "lightweight-charts";
import { candlesFor } from "@/lib/trading";

type CandlePoint = {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
};

type VolumePoint = {
  time: UTCTimestamp;
  value: number;
  color: string;
};

const BAR_SECONDS = 300;

function volumeColor(close: number, open: number) {
  return close >= open ? "rgba(45,212,167,.35)" : "rgba(255,107,122,.35)";
}

function bucketTime(epochMs: number): UTCTimestamp {
  return (Math.floor(epochMs / 1000 / BAR_SECONDS) * BAR_SECONDS) as UTCTimestamp;
}

export function TradingChart({
  price,
  livePrice,
  height = 410,
  ariaLabel = "Five minute candlestick and volume chart"
}: {
  price: number;
  livePrice?: number;
  height?: number;
  ariaLabel?: string;
}) {
  const container = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const lastCandle = useRef<CandlePoint | null>(null);
  const lastVolume = useRef<VolumePoint | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const chart = createChart(container.current, {
      autoSize: true,
      height,
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#93a0b4" },
      grid: { vertLines: { color: "rgba(148,163,184,.08)" }, horzLines: { color: "rgba(148,163,184,.08)" } },
      rightPriceScale: { borderColor: "rgba(148,163,184,.18)" },
      timeScale: { borderColor: "rgba(148,163,184,.18)", timeVisible: true }
    });
    const seed = candlesFor(price);
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#2dd4a7",
      downColor: "#ff6b7a",
      wickUpColor: "#2dd4a7",
      wickDownColor: "#ff6b7a",
      borderVisible: false
    });
    const candleData: CandlePoint[] = seed.map((item) => ({
      time: item.time as UTCTimestamp,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close
    }));
    candleSeries.setData(candleData);
    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: ""
    });
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
    const volumeData: VolumePoint[] = seed.map((item) => ({
      time: item.time as UTCTimestamp,
      value: item.volume,
      color: volumeColor(item.close, item.open)
    }));
    volume.setData(volumeData);
    chart.timeScale().fitContent();

    chartRef.current = chart;
    candleRef.current = candleSeries;
    volumeRef.current = volume;
    lastCandle.current = candleData[candleData.length - 1] ?? null;
    lastVolume.current = volumeData[volumeData.length - 1] ?? null;

    const observer = new ResizeObserver(() => chart.timeScale().scrollToRealTime());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
      lastCandle.current = null;
      lastVolume.current = null;
    };
  }, [height, price]);

  useEffect(() => {
    if (livePrice == null || !Number.isFinite(livePrice) || livePrice <= 0) return;
    const candles = candleRef.current;
    const volumes = volumeRef.current;
    const previous = lastCandle.current;
    const previousVolume = lastVolume.current;
    if (!candles || !volumes || !previous || !previousVolume) return;

    const time = bucketTime(Date.now());
    if (time > previous.time) {
      const next: CandlePoint = {
        time,
        open: previous.close,
        high: Math.max(previous.close, livePrice),
        low: Math.min(previous.close, livePrice),
        close: livePrice
      };
      const nextVolume: VolumePoint = {
        time,
        value: Math.max(1_000, Math.round(previousVolume.value * (0.85 + Math.random() * 0.4))),
        color: volumeColor(next.close, next.open)
      };
      candles.update(next);
      volumes.update(nextVolume);
      lastCandle.current = next;
      lastVolume.current = nextVolume;
      chartRef.current?.timeScale().scrollToRealTime();
      return;
    }

    const updated: CandlePoint = {
      time: previous.time,
      open: previous.open,
      high: Math.max(previous.high, livePrice),
      low: Math.min(previous.low, livePrice),
      close: livePrice
    };
    const updatedVolume: VolumePoint = {
      ...previousVolume,
      value: previousVolume.value + Math.round(80 + Math.random() * 220),
      color: volumeColor(updated.close, updated.open)
    };
    candles.update(updated);
    volumes.update(updatedVolume);
    lastCandle.current = updated;
    lastVolume.current = updatedVolume;
  }, [livePrice]);

  return <div ref={container} className="tradingChart" style={{ height }} aria-label={ariaLabel} />;
}
