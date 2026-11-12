import { describe, expect, it } from "vitest";
import { PLAYGROUND_STEPS, isPlaygroundComplete, playgroundProgress } from "./playground";

describe("playground progress", () => {
  it("starts at zero", () => {
    expect(playgroundProgress([])).toBe(0);
    expect(isPlaygroundComplete([])).toBe(false);
  });

  it("tracks partial and full completion", () => {
    expect(playgroundProgress(["paper-capital", "sample-trade"])).toBe(40);
    const all = PLAYGROUND_STEPS.map((step) => step.id);
    expect(playgroundProgress(all)).toBe(100);
    expect(isPlaygroundComplete(all)).toBe(true);
  });

  it("ignores duplicate step ids when scoring", () => {
    expect(playgroundProgress(["paper-capital", "paper-capital", "sample-trade"])).toBe(40);
  });
});
