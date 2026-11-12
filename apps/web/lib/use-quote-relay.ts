"use client";

import { useEffect, useState } from "react";
import {
  fetchRelayQuotes,
  relayQuoteSchema,
  relayStreamUrl,
  type RelayQuote
} from "@/lib/quote-relay";

export function useQuoteRelay(preferredSymbol?: string) {
  const [quotes, setQuotes] = useState<RelayQuote[]>([]);
  const [provider, setProvider] = useState("connecting");
  const [symbol, setSymbol] = useState(preferredSymbol ?? "AAPL");
  const [status, setStatus] = useState<"connecting" | "live" | "demo" | "error">("connecting");

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | undefined;
    let timer: ReturnType<typeof setInterval> | undefined;

    const applyQuote = (quote: RelayQuote) => {
      setQuotes((current) => {
        const next = current.filter((item) => item.symbol !== quote.symbol);
        next.push(quote);
        next.sort((a, b) => a.symbol.localeCompare(b.symbol));
        return next;
      });
    };

    const startLocalDemo = (seed: RelayQuote[]) => {
      setStatus("demo");
      setProvider("simulated-local");
      setQuotes(seed);
      timer = setInterval(() => {
        setQuotes((current) =>
          current.map((item) => {
            const last = Math.max(0.01, item.last * (1 + (Math.random() - 0.5) * 0.001));
            return {
              ...item,
              last: Number(last.toFixed(4)),
              change_pct: Number((((last - item.last) / item.last) * 100 + item.change_pct * 0.8).toFixed(4)),
              as_of: new Date().toISOString(),
              source: "simulated"
            };
          })
        );
      }, 1200);
    };

    void (async () => {
      try {
        const snapshot = await fetchRelayQuotes();
        if (cancelled) return;
        setProvider(snapshot.provider);
        setQuotes(snapshot.quotes);
        if (!preferredSymbol && snapshot.quotes[0]) {
          setSymbol(snapshot.quotes[0].symbol);
        }
        const url = relayStreamUrl();
        if (!url) {
          startLocalDemo(snapshot.quotes);
          return;
        }
        socket = new WebSocket(url);
        socket.onopen = () => setStatus("live");
        socket.onmessage = (event) => {
          const payload = JSON.parse(event.data as string) as {
            type?: string;
            provider?: string;
            quote?: unknown;
          };
          if (payload.type === "hello" && payload.provider) {
            setProvider(payload.provider);
            setStatus("live");
          }
          if (payload.type === "quote" && payload.quote) {
            const parsed = relayQuoteSchema.safeParse(payload.quote);
            if (parsed.success) applyQuote(parsed.data);
          }
        };
        socket.onerror = () => {
          socket?.close();
          if (!timer) startLocalDemo(snapshot.quotes);
        };
        socket.onclose = () => {
          if (!cancelled && !timer) startLocalDemo(snapshot.quotes);
        };
      } catch {
        if (!cancelled) {
          setStatus("error");
          const fallback = await fetchRelayQuotes().catch(() => ({ provider: "simulated-local", quotes: [] as RelayQuote[] }));
          startLocalDemo(fallback.quotes.length ? fallback.quotes : [
            { symbol: "AAPL", last: 228.4, change_pct: 0, as_of: new Date().toISOString(), source: "simulated", delayed: false }
          ]);
        }
      }
    })();

    return () => {
      cancelled = true;
      socket?.close();
      if (timer) clearInterval(timer);
    };
  }, [preferredSymbol]);

  const active = quotes.find((item) => item.symbol === symbol) ?? quotes[0] ?? null;
  return { quotes, provider, status, symbol, setSymbol, active };
}
