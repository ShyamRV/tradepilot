BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE membership_role AS ENUM ('owner', 'admin', 'analyst', 'viewer');
CREATE TYPE data_quality_status AS ENUM ('valid', 'stale', 'incomplete', 'quarantined');
CREATE TYPE job_status AS ENUM ('queued', 'running', 'succeeded', 'failed', 'cancelled');
CREATE TYPE paper_trade_status AS ENUM ('pending_next_session', 'open', 'closed', 'cancelled', 'rejected');

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL,
  password_hash text NOT NULL,
  display_name text,
  disabled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT users_email_normalized CHECK (email = lower(btrim(email))),
  CONSTRAINT users_email_unique UNIQUE (email)
);

CREATE TABLE workspaces (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE workspace_memberships (
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role membership_role NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);

-- Stable internal identity. Symbols belong in time-bounded aliases.
CREATE TABLE instruments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  market text NOT NULL CHECK (market IN ('crypto', 'equity', 'forex')),
  canonical_name text NOT NULL,
  base_currency text,
  quote_currency text,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE instrument_aliases (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  provider text NOT NULL,
  venue text NOT NULL DEFAULT '',
  vendor_instrument_id text NOT NULL,
  symbol text NOT NULL,
  valid_from timestamptz NOT NULL,
  valid_to timestamptz,
  currency text,
  price_multiplier numeric(30, 12) NOT NULL DEFAULT 1 CHECK (price_multiplier > 0),
  CHECK (valid_to IS NULL OR valid_to > valid_from),
  UNIQUE (provider, venue, vendor_instrument_id, valid_from)
);

CREATE TABLE dataset_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  entitlement_reference text NOT NULL,
  mode text NOT NULL CHECK (mode IN ('delayed', 'end_of_day')),
  delay_minutes integer NOT NULL CHECK (delay_minutes >= 0),
  schema_version text NOT NULL,
  object_uri text NOT NULL,
  sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  window_start timestamptz NOT NULL,
  window_end timestamptz NOT NULL,
  retrieved_at timestamptz NOT NULL,
  quality_status data_quality_status NOT NULL,
  supersedes_id uuid REFERENCES dataset_versions(id),
  correction_reason text,
  manifest jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (window_end > window_start),
  CHECK ((supersedes_id IS NULL) = (correction_reason IS NULL)),
  CHECK (jsonb_typeof(manifest) = 'object')
);

CREATE TABLE candles (
  dataset_version_id uuid NOT NULL REFERENCES dataset_versions(id),
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  timeframe text NOT NULL CHECK (timeframe IN ('15m', '1h', '4h', '1d')),
  opened_at timestamptz NOT NULL,
  open numeric(30, 12) NOT NULL CHECK (open > 0),
  high numeric(30, 12) NOT NULL CHECK (high > 0),
  low numeric(30, 12) NOT NULL CHECK (low > 0),
  close numeric(30, 12) NOT NULL CHECK (close > 0),
  volume numeric(38, 12) NOT NULL CHECK (volume >= 0),
  provider_sequence text,
  PRIMARY KEY (dataset_version_id, instrument_id, timeframe, opened_at),
  CHECK (high >= GREATEST(open, close, low)),
  CHECK (low <= LEAST(open, close, high))
);

CREATE TABLE strategies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, id)
);

CREATE TABLE strategy_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  strategy_id uuid NOT NULL,
  version integer NOT NULL CHECK (version > 0),
  definition jsonb NOT NULL CHECK (jsonb_typeof(definition) = 'object'),
  definition_sha256 text NOT NULL CHECK (definition_sha256 ~ '^[0-9a-f]{64}$'),
  engine_version text NOT NULL,
  validation_result jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (workspace_id, strategy_id) REFERENCES strategies(workspace_id, id) ON DELETE CASCADE,
  UNIQUE (strategy_id, version),
  UNIQUE (workspace_id, id)
);

CREATE TABLE risk_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  version integer NOT NULL CHECK (version > 0),
  limits jsonb NOT NULL CHECK (jsonb_typeof(limits) = 'object'),
  formula_version text NOT NULL,
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, version),
  UNIQUE (workspace_id, id)
);

CREATE TABLE analysis_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  dataset_version_id uuid NOT NULL REFERENCES dataset_versions(id),
  strategy_version_id uuid NOT NULL,
  risk_profile_id uuid,
  as_of timestamptz NOT NULL,
  data_status data_quality_status NOT NULL,
  result jsonb NOT NULL CHECK (jsonb_typeof(result) = 'object'),
  explanation_model text,
  prompt_template_version text,
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (workspace_id, strategy_version_id) REFERENCES strategy_versions(workspace_id, id),
  FOREIGN KEY (workspace_id, risk_profile_id) REFERENCES risk_profiles(workspace_id, id),
  UNIQUE (workspace_id, id)
);

CREATE TABLE risk_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  analysis_id uuid,
  risk_profile_id uuid NOT NULL,
  decision text NOT NULL CHECK (decision IN ('allow_paper', 'reject', 'not_evaluated')),
  inputs jsonb NOT NULL CHECK (jsonb_typeof(inputs) = 'object'),
  outputs jsonb NOT NULL CHECK (jsonb_typeof(outputs) = 'object'),
  formula_version text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (workspace_id, analysis_id) REFERENCES analysis_results(workspace_id, id),
  FOREIGN KEY (workspace_id, risk_profile_id) REFERENCES risk_profiles(workspace_id, id),
  UNIQUE (workspace_id, id)
);

CREATE TABLE paper_portfolios (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  name text NOT NULL,
  base_currency text NOT NULL,
  starting_cash numeric(30, 12) NOT NULL CHECK (starting_cash > 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (workspace_id, id)
);

CREATE TABLE paper_trades (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  portfolio_id uuid NOT NULL,
  analysis_id uuid NOT NULL,
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  dataset_version_id uuid NOT NULL REFERENCES dataset_versions(id),
  status paper_trade_status NOT NULL DEFAULT 'pending_next_session',
  side text NOT NULL CHECK (side = 'long'),
  quantity numeric(30, 12) NOT NULL CHECK (quantity > 0),
  signal_at timestamptz NOT NULL,
  eligible_fill_at timestamptz NOT NULL,
  opened_at timestamptz,
  open_price numeric(30, 12),
  closed_at timestamptz,
  close_price numeric(30, 12),
  fee_amount numeric(30, 12) NOT NULL DEFAULT 0 CHECK (fee_amount >= 0),
  slippage_bps numeric(12, 4) NOT NULL DEFAULT 0 CHECK (slippage_bps >= 0),
  idempotency_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (workspace_id, portfolio_id) REFERENCES paper_portfolios(workspace_id, id),
  FOREIGN KEY (workspace_id, analysis_id) REFERENCES analysis_results(workspace_id, id),
  CHECK (eligible_fill_at > signal_at),
  CHECK ((opened_at IS NULL) = (open_price IS NULL)),
  CHECK ((closed_at IS NULL) = (close_price IS NULL)),
  UNIQUE (workspace_id, id),
  UNIQUE (workspace_id, idempotency_key)
);

CREATE TABLE backtest_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  strategy_version_id uuid NOT NULL,
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  dataset_version_id uuid NOT NULL REFERENCES dataset_versions(id),
  status job_status NOT NULL DEFAULT 'queued',
  assumptions jsonb NOT NULL CHECK (jsonb_typeof(assumptions) = 'object'),
  metrics jsonb,
  artifact_uri text,
  error_code text,
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  FOREIGN KEY (workspace_id, strategy_version_id) REFERENCES strategy_versions(workspace_id, id),
  UNIQUE (workspace_id, id)
);

CREATE TABLE watchlist_items (
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  created_by uuid NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, instrument_id)
);

CREATE TABLE analysis_explanations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  analysis_id uuid NOT NULL,
  explanation jsonb NOT NULL CHECK (jsonb_typeof(explanation) = 'object'),
  model_version text NOT NULL,
  prompt_template_version text NOT NULL,
  fallback boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (workspace_id, analysis_id) REFERENCES analysis_results(workspace_id, id),
  UNIQUE (workspace_id, analysis_id),
  UNIQUE (workspace_id, id)
);

CREATE TABLE workspace_controls (
  workspace_id uuid PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
  quotas jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(quotas) = 'object'),
  feature_flags jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(feature_flags) = 'object'),
  updated_by uuid NOT NULL REFERENCES users(id),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  analysis_id uuid,
  channel text NOT NULL CHECK (channel IN ('dashboard', 'telegram', 'email')),
  recipient_ref text NOT NULL,
  payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  idempotency_key text NOT NULL,
  status text NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'suppressed', 'possibly_duplicated')),
  provider_message_id text,
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  sent_at timestamptz,
  FOREIGN KEY (workspace_id, analysis_id) REFERENCES analysis_results(workspace_id, id),
  UNIQUE (workspace_id, id),
  UNIQUE (workspace_id, channel, idempotency_key)
);

CREATE TABLE outbox_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  aggregate_type text NOT NULL,
  aggregate_id uuid NOT NULL,
  event_type text NOT NULL,
  payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  idempotency_key text NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  published_at timestamptz,
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  last_error text,
  UNIQUE (workspace_id, id),
  UNIQUE (workspace_id, idempotency_key)
);

CREATE TABLE audit_logs (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  workspace_id uuid REFERENCES workspaces(id) ON DELETE SET NULL,
  actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  action text NOT NULL,
  target_type text NOT NULL,
  target_id text,
  reason text,
  request_id text,
  ip_hash text,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  CHECK (jsonb_typeof(details) = 'object')
);

CREATE INDEX candles_lookup_idx ON candles (instrument_id, timeframe, opened_at);
CREATE INDEX analysis_workspace_created_idx ON analysis_results (workspace_id, created_at DESC);
CREATE INDEX backtests_workspace_created_idx ON backtest_runs (workspace_id, created_at DESC);
CREATE INDEX paper_trades_workspace_status_idx ON paper_trades (workspace_id, status);
CREATE INDEX outbox_unpublished_idx ON outbox_events (occurred_at) WHERE published_at IS NULL;
CREATE INDEX audit_workspace_time_idx ON audit_logs (workspace_id, occurred_at DESC);

CREATE FUNCTION app_user_id() RETURNS uuid
LANGUAGE sql STABLE PARALLEL SAFE
AS $$ SELECT nullif(current_setting('app.user_id', true), '')::uuid $$;

CREATE FUNCTION app_workspace_id() RETURNS uuid
LANGUAGE sql STABLE PARALLEL SAFE
AS $$ SELECT nullif(current_setting('app.workspace_id', true), '')::uuid $$;

CREATE FUNCTION is_workspace_member(target_workspace uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1 FROM workspace_memberships m
    WHERE m.workspace_id = target_workspace AND m.user_id = app_user_id()
  )
$$;

REVOKE ALL ON FUNCTION is_workspace_member(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION is_workspace_member(uuid) TO PUBLIC;

ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_memberships ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_member_select ON workspaces
  FOR SELECT USING (id = app_workspace_id() AND is_workspace_member(id));
CREATE POLICY membership_member_select ON workspace_memberships
  FOR SELECT USING (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id));

-- Creation is handled by a transaction/security-definer service function so the
-- initial owner membership can be inserted atomically. No direct app INSERT policy.

DO $$
DECLARE
  table_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'strategies', 'strategy_versions', 'risk_profiles', 'analysis_results',
    'risk_decisions', 'paper_portfolios', 'paper_trades', 'backtest_runs',
    'watchlist_items', 'analysis_explanations', 'workspace_controls',
    'notifications', 'outbox_events'
  ]
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
    EXECUTE format(
      'CREATE POLICY tenant_select ON %I FOR SELECT USING (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id))',
      table_name
    );
    EXECUTE format(
      'CREATE POLICY tenant_insert ON %I FOR INSERT WITH CHECK (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id))',
      table_name
    );
    EXECUTE format(
      'CREATE POLICY tenant_update ON %I FOR UPDATE USING (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id)) WITH CHECK (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id))',
      table_name
    );
    EXECUTE format(
      'CREATE POLICY tenant_delete ON %I FOR DELETE USING (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id))',
      table_name
    );
  END LOOP;
END $$;

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_tenant_select ON audit_logs
  FOR SELECT USING (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id));
CREATE POLICY audit_tenant_insert ON audit_logs
  FOR INSERT WITH CHECK (
    (workspace_id = app_workspace_id() AND is_workspace_member(workspace_id))
    OR workspace_id IS NULL
  );
-- Audit rows are append-only to application roles: no UPDATE/DELETE policies.

CREATE FUNCTION reject_immutable_change() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is immutable; create a superseding version', TG_TABLE_NAME;
END $$;

CREATE TRIGGER dataset_versions_immutable
BEFORE UPDATE OR DELETE ON dataset_versions
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER candles_immutable
BEFORE UPDATE OR DELETE ON candles
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER strategy_versions_immutable
BEFORE UPDATE OR DELETE ON strategy_versions
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER risk_profiles_immutable
BEFORE UPDATE OR DELETE ON risk_profiles
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER analysis_results_immutable
BEFORE UPDATE OR DELETE ON analysis_results
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER analysis_explanations_immutable
BEFORE UPDATE OR DELETE ON analysis_explanations
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER risk_decisions_immutable
BEFORE UPDATE OR DELETE ON risk_decisions
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

CREATE TRIGGER audit_logs_immutable
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

COMMENT ON DATABASE tradepilot IS 'TradePilot delayed/EOD analysis and paper-trading data';
COMMENT ON TABLE dataset_versions IS 'Immutable licensed dataset manifests; corrections supersede rather than mutate';
COMMENT ON TABLE candles IS 'Immutable observations pinned to a dataset version';
COMMENT ON TABLE paper_trades IS 'Simulation only; no broker execution authority';

COMMIT;
