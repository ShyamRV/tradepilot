import { z } from "zod";

export const instruments = [
  { exchange: "NSE", symbol: "RELIANCE", name: "Reliance Industries", price: 1532.4, change: 1.24 },
  { exchange: "NSE", symbol: "TCS", name: "Tata Consultancy Services", price: 3208.15, change: -0.38 },
  { exchange: "NSE", symbol: "INFY", name: "Infosys", price: 1487.7, change: 2.11 },
  { exchange: "NSE", symbol: "HDFCBANK", name: "HDFC Bank", price: 1761.2, change: 0.72 },
  { exchange: "BSE", symbol: "500325", name: "Reliance Industries", price: 1531.85, change: 1.19 }
] as const;

export type Instrument = (typeof instruments)[number];
export type Tick = { price: number; change: number; asOf: string; source: "stream" | "demo" };

export const orderSchema = z
  .object({
    side: z.enum(["BUY", "SELL"]),
    type: z.enum(["MARKET", "LIMIT"]),
    quantity: z.coerce.number().int().positive().max(100_000),
    limitPrice: z.coerce.number().positive().optional(),
    product: z.enum(["CNC", "MIS"])
  })
  .superRefine((value, context) => {
    if (value.type === "LIMIT" && !value.limitPrice) {
      context.addIssue({ code: "custom", path: ["limitPrice"], message: "Limit price is required." });
    }
  });

export type OrderInput = z.infer<typeof orderSchema>;
export type PaperOrder = OrderInput & {
  id: string;
  exchange: string;
  symbol: string;
  status: "OPEN" | "FILLED" | "CANCELLED" | "REJECTED";
  price: number;
  placedAt: string;
};

export const agentSchema = z.object({
  name: z.string().trim().min(3).max(50),
  strategy: z.enum(["Momentum", "Mean reversion", "Breakout"]),
  risk: z.enum(["Conservative", "Balanced", "Aggressive"]),
  universe: z.string().trim().min(2).max(120),
  capital: z.coerce.number().positive().max(10_000_000),
  dailyLoss: z.coerce.number().positive()
}).refine((value) => value.dailyLoss < value.capital, {
  path: ["dailyLoss"],
  message: "Daily loss must be below allocated capital."
});

export type AgentInput = z.infer<typeof agentSchema>;
export type TradingAgent = AgentInput & {
  id: string;
  status: "RUNNING" | "PAUSED" | "KILLED";
  pnl: number;
  createdAt: string;
  decisions: Array<{ time: string; signal: string; rationale: string; checks: string; result: string }>;
};

export function candlesFor(base: number) {
  const now = Math.floor(Date.now() / 1000);
  return Array.from({ length: 96 }, (_, index) => {
    const wave = Math.sin(index / 7) * base * 0.009;
    const drift = index * base * 0.00008;
    const open = base + wave + drift;
    const close = open + Math.sin(index * 1.7) * base * 0.003;
    return {
      time: (now - (95 - index) * 300) as number,
      open,
      high: Math.max(open, close) + base * 0.002,
      low: Math.min(open, close) - base * 0.002,
      close,
      volume: 20_000 + ((index * 7919) % 90_000)
    };
  });
}

export function portfolioSeries() {
  return Array.from({ length: 30 }, (_, index) => ({
    day: `${index + 1}`,
    equity: 980_000 + index * 900 + Math.sin(index / 3) * 13_000,
    benchmark: 980_000 + index * 620 + Math.sin(index / 4) * 7_000
  }));
}
