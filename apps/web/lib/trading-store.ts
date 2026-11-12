"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AgentInput, PaperOrder, TradingAgent } from "@/lib/trading";

type TradingState = {
  watchlist: string[];
  orders: PaperOrder[];
  agents: TradingAgent[];
  toggleWatch: (symbol: string) => void;
  placeOrder: (
    order: Omit<PaperOrder, "id" | "status" | "placedAt">,
    status?: PaperOrder["status"]
  ) => PaperOrder;
  cancelOrder: (id: string) => void;
  createAgent: (input: AgentInput) => TradingAgent;
  setAgentStatus: (id: string, status: TradingAgent["status"]) => void;
};

const seedAgents: TradingAgent[] = [
  {
    id: "trend-navigator",
    name: "Trend Navigator",
    strategy: "Momentum",
    risk: "Balanced",
    universe: "NIFTY 50",
    capital: 250000,
    dailyLoss: 5000,
    horizon: "intraday",
    stopRule: "or_mid",
    targetR: 1,
    autonomyMode: "delegated",
    status: "RUNNING",
    pnl: 3840,
    createdAt: new Date().toISOString(),
    lastStage: "ready",
    decisions: [
      {
        time: "14:42 IST",
        signal: "INFY trend confirmation",
        rationale: "Price held above VWAP with expanding volume; waited for confirmation.",
        checks: "Liquidity, exposure and daily-loss limits passed",
        result: "Paper BUY · 12 shares"
      },
      {
        time: "13:18 IST",
        signal: "TCS exit threshold",
        rationale: "Momentum weakened below the configured trailing level.",
        checks: "Position ownership and market-hours checks passed",
        result: "Paper SELL · 5 shares"
      }
    ]
  }
];

export const useTradingStore = create<TradingState>()(
  persist(
    (set) => ({
      watchlist: ["RELIANCE", "TCS", "INFY", "HDFCBANK"],
      orders: [],
      agents: seedAgents,
      toggleWatch: (symbol) =>
        set((state) => ({
          watchlist: state.watchlist.includes(symbol)
            ? state.watchlist.filter((item) => item !== symbol)
            : [...state.watchlist, symbol]
        })),
      placeOrder: (input, requestedStatus) => {
        const order: PaperOrder = {
          ...input,
          id: crypto.randomUUID(),
          status: requestedStatus ?? (input.type === "MARKET" ? "FILLED" : "OPEN"),
          placedAt: new Date().toISOString()
        };
        set((state) => ({ orders: [order, ...state.orders] }));
        return order;
      },
      cancelOrder: (id) =>
        set((state) => ({
          orders: state.orders.map((order) => (order.id === id ? { ...order, status: "CANCELLED" } : order))
        })),
      createAgent: (input) => {
        const agent: TradingAgent = {
          ...input,
          id: crypto.randomUUID(),
          status: "PAUSED",
          pnl: 0,
          createdAt: new Date().toISOString(),
          decisions: []
        };
        set((state) => ({ agents: [agent, ...state.agents] }));
        return agent;
      },
      setAgentStatus: (id, status) =>
        set((state) => ({
          agents: state.agents.map((agent) => (agent.id === id ? { ...agent, status } : agent))
        }))
    }),
    {
      name: "tradepilot.trading",
      partialize: (state) => ({ watchlist: state.watchlist, orders: state.orders, agents: state.agents })
    }
  )
);
