import { expect, test } from "@playwright/test";

test("terminal shows simulated stream, chart, depth, and order preview", async ({ page }) => {
  await page.goto("/terminal/NSE/RELIANCE");
  await expect(page.getByRole("heading", { name: "RELIANCE" })).toBeVisible();
  await expect(page.getByLabel("Five minute candlestick and volume chart")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Market depth" })).toBeVisible();
  await expect(page.getByText("Paper trading only", { exact: true })).toBeVisible();
  await page.getByTestId("preview-order").click();
  await expect(page.getByRole("heading", { name: "Review paper order" })).toBeVisible();
  await expect(page.getByText(/Prices, fills, slippage, fees and taxes are simulated/)).toBeVisible();
});

test("agent can be created paused and permanently killed in demo mode", async ({ page }) => {
  await page.goto("/agents/new");
  await page.getByRole("textbox", { name: "Agent name" }).fill("Guarded Momentum");
  await page.getByRole("textbox", { name: "Trading universe" }).fill("INFY,TCS");
  await page.getByLabel("Risk profile").selectOption({ label: "Balanced" });
  await page.getByRole("button", { name: "Create paused agent" }).click();
  await expect(page).toHaveURL(/\/agents\/(?!new(?:\?|$))/);
  await expect(page.getByRole("heading", { name: "Guarded Momentum" })).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Kill agent" }).click();
  await page.getByRole("button", { name: "Kill permanently" }).click();
  await expect(page.getByText("KILLED", { exact: true })).toBeVisible();
});
