import { describe, expect, it } from "vitest";
import { agentSchema, orderSchema } from "./trading";

describe("paper order validation", () => {
  it("accepts a valid market order", () => {
    const result = orderSchema.safeParse({ side: "BUY", type: "MARKET", quantity: "10", product: "CNC" });
    expect(result.success).toBe(true);
  });

  it("requires a price for limit orders", () => {
    const result = orderSchema.safeParse({ side: "SELL", type: "LIMIT", quantity: 2, product: "MIS" });
    expect(result.success).toBe(false);
  });

  it("rejects non-positive quantities", () => {
    const result = orderSchema.safeParse({ side: "BUY", type: "MARKET", quantity: 0, product: "CNC" });
    expect(result.success).toBe(false);
  });
});

describe("agent guardrail validation", () => {
  it("requires the daily stop below allocated capital", () => {
    const result = agentSchema.safeParse({
      name: "Trend Agent",
      strategy: "Momentum",
      risk: "Balanced",
      universe: "NIFTY 50",
      capital: 10000,
      dailyLoss: 10000
    });
    expect(result.success).toBe(false);
  });
});
