BEGIN;

-- Additive runtime tables for the MVP Repository/AuthProvider adapters.
-- Kept separate from domain tables in 0001_initial.sql to avoid enum/shape conflicts
-- while still supporting durable sessions, document storage, outbox, and audit.

CREATE TABLE IF NOT EXISTS app_users (
  id text PRIMARY KEY,
  email text NOT NULL,
  salt bytea NOT NULL,
  password_hash bytea NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT app_users_email_normalized CHECK (email = lower(btrim(email))),
  CONSTRAINT app_users_email_unique UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS auth_sessions (
  token_hash text PRIMARY KEY,
  user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_workspaces (
  id text PRIMARY KEY,
  name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 120),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app_memberships (
  workspace_id text NOT NULL REFERENCES app_workspaces(id) ON DELETE CASCADE,
  user_id text NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('owner', 'publisher', 'auditor', 'member')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS app_documents (
  bucket text NOT NULL,
  tenant_id text NOT NULL,
  doc_key text NOT NULL,
  value bytea NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (bucket, tenant_id, doc_key)
);

CREATE TABLE IF NOT EXISTS app_audit_events (
  id text PRIMARY KEY,
  tenant_id text NOT NULL,
  actor_id text NOT NULL,
  action text NOT NULL,
  resource text NOT NULL,
  occurred_at timestamptz NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS app_outbox (
  id text PRIMARY KEY,
  tenant_id text NOT NULL,
  topic text NOT NULL,
  payload jsonb NOT NULL,
  created_at timestamptz NOT NULL,
  sent boolean NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS app_workspace_controls (
  workspace_id text PRIMARY KEY REFERENCES app_workspaces(id) ON DELETE CASCADE,
  quotas jsonb NOT NULL DEFAULT '{}'::jsonb,
  feature_flags jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS app_outbox_pending_idx ON app_outbox (created_at) WHERE sent = false;
CREATE INDEX IF NOT EXISTS app_audit_tenant_time_idx ON app_audit_events (tenant_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS app_documents_tenant_bucket_idx ON app_documents (tenant_id, bucket);

COMMIT;
