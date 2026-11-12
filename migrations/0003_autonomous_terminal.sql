BEGIN;

-- Queryable projections for the autonomous terminal. The current Repository
-- remains compatible through app_documents; these tables support a later
-- adapter migration without changing domain IDs or Decimal precision.
CREATE TABLE IF NOT EXISTS app_trading_agents (
  id text PRIMARY KEY,
  workspace_id text NOT NULL,
  name text NOT NULL,
  status text NOT NULL CHECK (status IN ('created', 'running', 'paused', 'stopped', 'killed')),
  config jsonb NOT NULL CHECK (jsonb_typeof(config) = 'object'),
  last_control_reason text,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS app_sandbox_orders (
  id text PRIMARY KEY,
  workspace_id text NOT NULL,
  agent_id text,
  symbol text NOT NULL,
  side text NOT NULL CHECK (side IN ('buy', 'sell')),
  order_type text NOT NULL CHECK (order_type IN ('market', 'limit')),
  quantity integer NOT NULL CHECK (quantity > 0),
  limit_price numeric(30, 12),
  status text NOT NULL CHECK (
    status IN ('created', 'risk_rejected', 'accepted', 'partially_filled', 'filled', 'cancelled', 'rejected')
  ),
  filled_quantity integer NOT NULL DEFAULT 0 CHECK (filled_quantity >= 0),
  average_fill_price numeric(30, 12),
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL,
  updated_at timestamptz NOT NULL,
  UNIQUE (workspace_id, id)
);

CREATE TABLE IF NOT EXISTS app_pretrade_risk_decisions (
  order_id text PRIMARY KEY,
  workspace_id text NOT NULL,
  outcome text NOT NULL CHECK (outcome IN ('allow', 'reject')),
  reasons jsonb NOT NULL CHECK (jsonb_typeof(reasons) = 'array'),
  reference_price numeric(30, 12) NOT NULL,
  order_value numeric(30, 12) NOT NULL,
  formula_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS app_agents_workspace_status_idx
  ON app_trading_agents (workspace_id, status);
CREATE INDEX IF NOT EXISTS app_sandbox_orders_workspace_time_idx
  ON app_sandbox_orders (workspace_id, created_at DESC);

COMMIT;
