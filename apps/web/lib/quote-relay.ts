import { z } from "zod";
import { API_URL } from "@/lib/api";

export const relayQuoteSchema = z.object({
  symbol: z.string(),
  last: z.coerce.number().positive(),
  change_pct: z.coerce.number(),
  as_of: z.string(),
  source: z.string(),
  delayed: z.boolean().optional().default(false)
});

export type RelayQuote = z.infer<typeof relayQuoteSchema>;

const snapshotSchema = z.object({
  provider: z.string(),
  quotes: z.array(relayQuoteSchema),
  disclaimer: z.string().optional()
});

export function relayStreamUrl() {
  if (!API_URL) return null;
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/v1/market/relay/stream`;
}

export async function fetchRelayQuotes(): Promise<{ provider: string; quotes: RelayQuote[] }> {
  if (!API_URL) {
    return {
      provider: "simulated-local",
      quotes: [
        { symbol: "AAPL", last: 228.4, change_pct: 0.12, as_of: new Date().toISOString(), source: "simulated", delayed: false },
        { symbol: "MSFT", last: 428.1, change_pct: -0.08, as_of: new Date().toISOString(), source: "simulated", delayed: false },
        { symbol: "NVDA", last: 131.2, change_pct: 0.35, as_of: new Date().toISOString(), source: "simulated", delayed: false },
        { symbol: "BINANCE:BTCUSDT", last: 67450, change_pct: 0.22, as_of: new Date().toISOString(), source: "simulated", delayed: false },
        { symbol: "BINANCE:ETHUSDT", last: 3280, change_pct: -0.15, as_of: new Date().toISOString(), source: "simulated", delayed: false }
      ]
    };
  }
  const response = await fetch(`${API_URL}/v1/market/relay/quotes`);
  if (!response.ok) throw new Error(`Relay quotes failed (${response.status})`);
  return snapshotSchema.parse(await response.json());
}
