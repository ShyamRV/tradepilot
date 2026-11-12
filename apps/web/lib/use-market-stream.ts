"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { marketStreamUrl, quotePayloadSchema } from "@/lib/trading-api";
import type { Tick } from "@/lib/trading";

export function useMarketStream(exchange: string, symbol: string, initialPrice: number) {
  const { apiConfigured, token, workspaceId } = useWorkspace();
  const [tick, setTick] = useState<Tick>({
    price: initialPrice,
    change: 0,
    asOf: new Date().toISOString(),
    source: "demo"
  });
  const [status, setStatus] = useState<"connecting" | "live" | "demo" | "stale">("connecting");

  useEffect(() => {
    const streamUrl =
      apiConfigured && token && workspaceId ? marketStreamUrl({ token, workspaceId }, symbol) : null;
    let socket: WebSocket | undefined;
    let timer: ReturnType<typeof setInterval> | undefined;
    let lastUpdate = Date.now();

    const demo = () => {
      setStatus("demo");
      timer = setInterval(() => {
        setTick((current) => {
          const next = Math.max(0.05, current.price * (1 + (Math.random() - 0.5) * 0.0007));
          lastUpdate = Date.now();
          return {
            price: next,
            change: ((next - initialPrice) / initialPrice) * 100,
            asOf: new Date().toISOString(),
            source: "demo"
          };
        });
      }, 1800);
    };

    if (!streamUrl) {
      demo();
    } else {
      try {
        socket = new WebSocket(streamUrl);
        socket.onopen = () => setStatus("live");
        socket.onmessage = (event) => {
          const parsed = quotePayloadSchema.safeParse(JSON.parse(event.data));
          if (!parsed.success) return;
          const payload = parsed.data;
          lastUpdate = Date.now();
          setTick({
            price: payload.last,
            change: ((payload.last - initialPrice) / initialPrice) * 100,
            asOf: payload.as_of,
            source: "stream"
          });
          setStatus("live");
        };
        socket.onerror = () => {
          socket?.close();
          if (!timer) demo();
        };
      } catch {
        demo();
      }
    }

    const staleCheck = setInterval(() => {
      if (Date.now() - lastUpdate > 15_000) {
        setStatus((current) => (current === "live" ? "stale" : current));
      }
    }, 5000);
    return () => {
      socket?.close();
      if (timer) clearInterval(timer);
      clearInterval(staleCheck);
    };
  }, [apiConfigured, exchange, initialPrice, symbol, token, workspaceId]);

  return { tick, status };
}
