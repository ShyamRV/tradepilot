# ADR 0005: Workspace tenancy enforced with RLS

- Status: Accepted
- Date: 2026-11-09

## Decision

Tenant-owned rows carry `workspace_id`. After authentication and membership authorization, the application starts a transaction and sets `SET LOCAL app.user_id` and `app.workspace_id`. PostgreSQL row-level security checks both values through membership-aware helper functions. Deployed application roles cannot bypass RLS, own tables, or use `BYPASSRLS`; migrations use a separate owner role. Privileged support access is time-bound, reason-coded, approved, and audited.

Background jobs carry a signed workspace/job identity and set the same context. Cross-workspace administration uses narrowly scoped security-definer functions, never disabled RLS.

## Consequences

API authorization remains required; RLS is defense in depth. Connection pooling must use transaction mode and transaction-local settings. CI must test cross-tenant reads, writes, joins, and guessed identifiers.
