export type Rule = {
  label: string;
  result: "pass" | "fail";
  evidence: string;
};

export type DashboardData = {
  workspace: { name: string; market: string; mode: string; updatedAt: string };
  freshness: { status: "delayed" | "eod"; asOf: string; delay: string };
  watchlist: Array<{ symbol: string; price: number; change: number; signal: string }>;
  strategies: Array<{ id: string; name: string; description: string; enabled: boolean; settings: string }>;
  analysis: { symbol: string; verdict: string; confidence: number; rules: Rule[] };
  risk: { decision: "Allowed" | "Blocked"; maxPosition: number; riskPerTrade: number; notes: string[] };
  portfolio: { cash: number; equity: number; pnl: number; positions: Array<{ symbol: string; quantity: number; average: number; last: number }> };
  history: Array<{ date: string; symbol: string; side: string; quantity: number; price: number; status: string }>;
  backtest: { returnPct: number; benchmarkPct: number; maxDrawdownPct: number; winRatePct: number; trades: number };
  notifications: Array<{ id: string; title: string; detail: string; time: string; level: "info" | "warning" }>;
  metadata: { source: string; asOf: string; adjustment: string; limitations: string };
};

export type Workspace = { id: string; name: string };
export type WorkspaceMembership = { workspace: Workspace; role: string };
export type AuthMode = "login" | "register";

export const demoDashboard: DashboardData = {
  workspace: { name: "NSE Equity Paper Lab", market: "NSE cash equities", mode: "Paper trading", updatedAt: "2026-11-09T15:30:00+05:30" },
  freshness: { status: "eod", asOf: "Nov 9, 2026 · 3:30 PM IST", delay: "Licensed end-of-day prices" },
  watchlist: [
    { symbol: "RELIANCE", price: 1532.4, change: 1.24, signal: "Watch" },
    { symbol: "TCS", price: 3208.15, change: -0.38, signal: "Hold" },
    { symbol: "INFY", price: 1487.7, change: 2.11, signal: "Candidate" },
    { symbol: "NIFTYBEES", price: 298.35, change: 0.42, signal: "Benchmark" }
  ],
  strategies: [
    { id: "momentum", name: "Trend confirmation", description: "Price above 50/200-day averages with volume support.", enabled: true, settings: "50/200 SMA · volume ≥ 1.2×" },
    { id: "pullback", name: "Quality pullback", description: "Controlled retracement within a primary uptrend.", enabled: false, settings: "RSI 40–55 · max stop 5%" }
  ],
  analysis: {
    symbol: "INFY",
    verdict: "Candidate",
    confidence: 78,
    rules: [
      { label: "Primary trend", result: "pass", evidence: "Close is 8.4% above 50-day SMA" },
      { label: "Volume confirmation", result: "pass", evidence: "1.34× 20-day average volume" },
      { label: "Extended price", result: "fail", evidence: "6.2% above preferred entry zone" },
      { label: "Corporate event proximity", result: "pass", evidence: "No recorded corporate event within 14 days" }
    ]
  },
  risk: { decision: "Allowed", maxPosition: 42000, riskPerTrade: 4000, notes: ["Illustrative stop: ₹1,432.70", "Portfolio heat after trade: 2.6%", "Size assumes 1% account risk"] },
  portfolio: {
    cash: 684200,
    equity: 1008400,
    pnl: 8400,
    positions: [
      { symbol: "RELIANCE", quantity: 100, average: 1498.1, last: 1532.4 },
      { symbol: "TCS", quantity: 50, average: 3157.5, last: 3208.15 }
    ]
  },
  history: [
    { date: "Nov 7", symbol: "TCS", side: "Buy", quantity: 50, price: 3157.5, status: "Filled" },
    { date: "Nov 3", symbol: "RELIANCE", side: "Buy", quantity: 100, price: 1498.1, status: "Filled" },
    { date: "Oct 28", symbol: "HDFCBANK", side: "Sell", quantity: 75, price: 1761.2, status: "Filled" }
  ],
  backtest: { returnPct: 16.8, benchmarkPct: 12.3, maxDrawdownPct: -8.1, winRatePct: 57, trades: 84 },
  notifications: [
    { id: "1", title: "INFY passed 3 of 4 rules", detail: "Rule counts are evidence checks, not probability of profit.", time: "3:35 PM", level: "info" },
    { id: "2", title: "Price data is EOD", detail: "Delayed/EOD only. Signals may differ from live market conditions.", time: "3:30 PM", level: "warning" }
  ],
  metadata: {
    source: "Demo market dataset (illustrative sample)",
    asOf: "November 9, 2026 NSE market close",
    adjustment: "Split and dividend adjusted where available",
    limitations:
      "Illustrative demo data only when NEXT_PUBLIC_API_URL is unset. Not investment advice; paper trading only; execution, slippage, taxes, and live liquidity are not modeled."
  }
};

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");

export const apiConfigured = Boolean(API_URL);

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string, workspaceId?: string): Promise<T> {
  if (!API_URL) throw new ApiError("The API URL is not configured.", 0);
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (workspaceId) headers.set("X-Workspace-ID", workspaceId);

  const response = await fetch(`${API_URL}${path}`, { ...options, headers, cache: "no-store" });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string | { code?: string } };
      if (typeof body.detail === "string") message = body.detail;
      else if (body.detail?.code) message = body.detail.code.replaceAll("_", " ");
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function authenticate(mode: AuthMode, email: string, password: string): Promise<string> {
  const credentials = JSON.stringify({ email, password });
  if (mode === "register") {
    await request("/v1/auth/register", { method: "POST", body: credentials });
  }
  const result = await request<{ access_token: string }>("/v1/auth/login", { method: "POST", body: credentials });
  return result.access_token;
}

export function listWorkspaces(token: string, signal?: AbortSignal): Promise<WorkspaceMembership[]> {
  return request("/v1/workspaces", { signal }, token);
}

export function createWorkspace(token: string, name: string): Promise<Workspace> {
  return request("/v1/workspaces", { method: "POST", body: JSON.stringify({ name }) }, token);
}

export function getDashboard(token: string, workspaceId: string, signal?: AbortSignal): Promise<DashboardData> {
  return request("/api/dashboard", { signal }, token, workspaceId);
}

export async function logout(token: string): Promise<void> {
  await request("/v1/auth/logout", { method: "POST" }, token);
}
