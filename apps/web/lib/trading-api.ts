import { z } from "zod";
import { API_URL, ApiError } from "@/lib/api";

export const quotePayloadSchema = z.object({
  symbol: z.string(),
  bid: z.coerce.number().positive(),
  ask: z.coerce.number().positive(),
  last: z.coerce.number().positive(),
  as_of: z.string(),
  sequence: z.number().int().positive(),
  provider: z.string()
});

const sandboxOrderSchema = z.object({
  status: z.string(),
  reason: z.string().nullable().optional(),
  filled_quantity: z.number().int().nonnegative().optional(),
  average_fill_price: z.coerce.number().nullable().optional()
}).passthrough();

export type SandboxOrderResult = z.infer<typeof sandboxOrderSchema>;
export type TradingSession = { token: string; workspaceId: string };

export const backendAgentSchema = z.object({
  id: z.string(),
  workspace_id: z.string(),
  status: z.enum(["created", "running", "paused", "stopped", "killed"]),
  config: z.object({
    name: z.string(),
    symbols: z.array(z.string()),
    strategy: z.string(),
    max_capital: z.coerce.number(),
    max_daily_loss: z.coerce.number(),
    horizon: z.string().optional(),
    setups: z.array(z.string()).optional(),
    stop_rule: z.string().optional(),
    target_r: z.coerce.number().optional(),
    autonomy_mode: z.string().optional(),
    flat_by_minute: z.number().nullable().optional()
  }),
  created_at: z.string(),
  updated_at: z.string(),
  last_control_reason: z.string().nullable(),
  last_pipeline_stage: z.string().nullable().optional(),
  daily_pnl: z.coerce.number().optional()
}).passthrough();
export type BackendAgent = z.infer<typeof backendAgentSchema>;
export const agentDecisionSchema = z.object({
  id: z.string(),
  agent_id: z.string(),
  signal: z.record(z.string(), z.unknown()),
  indicators: z.array(z.record(z.string(), z.unknown())),
  rationale: z.record(z.string(), z.unknown()),
  risk_checks: z.array(z.record(z.string(), z.unknown())),
  authority_version: z.string(),
  resulting_order_id: z.string().nullable(),
  created_at: z.string()
});
export type BackendAgentDecision = z.infer<typeof agentDecisionSchema>;

function headers(session: TradingSession) {
  return {
    "content-type": "application/json",
    authorization: `Bearer ${session.token}`,
    "x-workspace-id": session.workspaceId
  };
}

export async function submitSandboxOrder(
  session: TradingSession,
  input: {
    idempotency_key: string;
    symbol: string;
    side: "buy" | "sell";
    quantity: number;
    order_type: "market" | "limit";
    limit_price?: string;
    equity: string;
    cash: string;
  }
): Promise<SandboxOrderResult> {
  if (!API_URL) throw new ApiError("Live API is not configured.", 0);
  const response = await fetch(`${API_URL}/v1/workspaces/${session.workspaceId}/sandbox/orders`, {
    method: "POST",
    headers: headers(session),
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new ApiError(`Sandbox order failed (${response.status}).`, response.status);
  return sandboxOrderSchema.parse(await response.json());
}

export function marketStreamUrl(session: TradingSession, symbol: string) {
  if (!API_URL) return null;
  const base = API_URL.replace(/^http/, "ws");
  return `${base}/v1/workspaces/${encodeURIComponent(session.workspaceId)}/market/stream/${encodeURIComponent(symbol)}?token=${encodeURIComponent(session.token)}`;
}

export async function listBackendAgents(session: TradingSession): Promise<BackendAgent[]> {
  if (!API_URL) return [];
  const response = await fetch(`${API_URL}/v1/workspaces/${session.workspaceId}/agents`, {
    headers: headers(session)
  });
  if (!response.ok) throw new ApiError(`Unable to load agents (${response.status}).`, response.status);
  return z.array(backendAgentSchema).parse(await response.json());
}

export async function createBackendAgent(
  session: TradingSession,
  input: {
    name: string;
    symbols: string[];
    strategy: string;
    max_capital: string;
    max_daily_loss: string;
    horizon?: string;
    setups?: string[];
    stop_rule?: string;
    target_r?: string;
    autonomy_mode?: string;
    flat_by_minute?: number | null;
  }
): Promise<BackendAgent> {
  if (!API_URL) throw new ApiError("Live API is not configured.", 0);
  const response = await fetch(`${API_URL}/v1/workspaces/${session.workspaceId}/agents`, {
    method: "POST",
    headers: headers(session),
    body: JSON.stringify(input)
  });
  if (!response.ok) throw new ApiError(`Unable to create agent (${response.status}).`, response.status);
  return backendAgentSchema.parse(await response.json());
}

export async function tickBackendAgents(session: TradingSession): Promise<{ results: unknown[] }> {
  if (!API_URL) throw new ApiError("Live API is not configured.", 0);
  const response = await fetch(`${API_URL}/v1/workspaces/${session.workspaceId}/agents/tick`, {
    method: "POST",
    headers: headers(session)
  });
  if (!response.ok) throw new ApiError(`Agent tick failed (${response.status}).`, response.status);
  return z.object({ results: z.array(z.unknown()) }).parse(await response.json());
}

export async function controlBackendAgent(
  session: TradingSession,
  agentId: string,
  action: "start" | "pause" | "resume" | "stop" | "kill",
  reason: string
): Promise<BackendAgent> {
  if (!API_URL) throw new ApiError("Live API is not configured.", 0);
  const response = await fetch(
    `${API_URL}/v1/workspaces/${session.workspaceId}/agents/${encodeURIComponent(agentId)}/control`,
    {
      method: "POST",
      headers: headers(session),
      body: JSON.stringify({ action, reason })
    }
  );
  if (!response.ok) throw new ApiError(`Agent control failed (${response.status}).`, response.status);
  return backendAgentSchema.parse(await response.json());
}

export async function listAgentDecisions(
  session: TradingSession,
  agentId: string
): Promise<BackendAgentDecision[]> {
  if (!API_URL) return [];
  const response = await fetch(
    `${API_URL}/v1/workspaces/${session.workspaceId}/agents/${encodeURIComponent(agentId)}/decisions`,
    { headers: headers(session) }
  );
  if (!response.ok) throw new ApiError(`Unable to load decision trace (${response.status}).`, response.status);
  return z.array(agentDecisionSchema).parse(await response.json());
}
