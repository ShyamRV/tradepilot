"use client";

import { useEffect, useId, useRef } from "react";

type Props = {
  scriptSrc: string;
  config: Record<string, unknown>;
  height?: number | string;
  title: string;
  className?: string;
};

/** Official TradingView embed: injects their script into a local container. */
export function TradingViewWidget({ scriptSrc, config, height = 420, title, className }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const reactId = useId().replace(/:/g, "");

  const configJson = JSON.stringify(config);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.innerHTML = "";

    const container = document.createElement("div");
    container.className = "tradingview-widget-container";
    container.style.height = typeof height === "number" ? `${height}px` : height;

    const widget = document.createElement("div");
    widget.className = "tradingview-widget-container__widget";
    widget.style.height = "100%";
    container.appendChild(widget);

    const script = document.createElement("script");
    script.src = scriptSrc;
    script.type = "text/javascript";
    script.async = true;
    script.dataset.tvId = reactId;
    script.innerHTML = configJson;
    container.appendChild(script);

    host.appendChild(container);
    return () => {
      host.innerHTML = "";
    };
  }, [configJson, height, reactId, scriptSrc]);

  return (
    <section className={`tvWidgetPanel ${className ?? ""}`.trim()} aria-label={title}>
      <header className="tvWidgetHeader">
        <h2>{title}</h2>
        <span className="delayBadge" title="TradingView delayed market data for Indian cash equities">
          15-min delayed
        </span>
      </header>
      <div ref={hostRef} className="tvWidgetHost" style={{ minHeight: typeof height === "number" ? height : undefined }} />
      <p className="chartCaption">
        Embedded TradingView widget · delayed Indian market data · not investment advice · Athena does not
        redistribute exchange feeds from this embed.
      </p>
    </section>
  );
}
