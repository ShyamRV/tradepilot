# Monitoring notes

## Structured logging

API and worker emit **JSON lines** to stdout when `LOG_LEVEL` is set (default
`INFO`). Fields include at least:

| Field | Meaning |
| --- | --- |
| `ts` | UTC ISO-8601 timestamp |
| `level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `service` | `api` or `worker` |
| `event` | Stable event name (no PII, no secrets, no raw prompts) |
| `request_id` | Present on HTTP requests when middleware assigns one |

Do not log bearer tokens, passwords, `TELEGRAM_BOT_TOKEN`, provider API keys,
raw LLM prompts, or full personal email addresses in production aggregators.

## Health endpoints

| Path | Purpose | Expected |
| --- | --- | --- |
| `GET /health` | Liveness — process is up | `200` `{"status":"ok"}` |
| `GET /ready` | Readiness — safe to receive traffic | `200` with `checks`; `503` when repository ping fails |

`/ready` calls repository `ping()` when available (Postgres/SQLite adapters) and
reports whether `DATABASE_URL` / `TRADEPILOT_DB_PATH` are configured.

Uptime / load-balancer probes:

- **Liveness** → `/health` (restart container if failing repeatedly)
- **Readiness** → `/ready` (remove from LB rotation if failing; do not restart
  solely on readiness flaps during dependency blips)

Compose, Railway, and Render blueprints probe `/ready` (Dockerfile image
HEALTHCHECK uses `/health` as a process liveness fallback).

## Sentry stub

`SENTRY_DSN` is reserved in `.env.example` and compose/host manifests.

- Empty / unset → no error reporting SDK is initialized (current default).
- When a project DSN is provisioned in the **secrets manager**, install and
  initialize `sentry-sdk` for FastAPI/worker in a follow-up change; keep PII
  scrubbing on; never send Authorization headers or market-data API keys.

Until then, treat `SENTRY_DSN` as a configuration stub only.

## Uptime checks

Configure an external uptime monitor (Better Stack, Pingdom, Checkly, Cloud
provider synthetic, etc.) against the **public HTTPS** API:

1. `GET https://<api-host>/health` every 60s from at least two regions.
2. After durable DB wiring: `GET https://<api-host>/ready` every 60s; alert on
   sustained non-200.
3. Page on: consecutive failures ≥3, TLS errors, or certificate expiry <14 days.
4. Keep the web (Vercel) check separate from the API check so a static demo
   outage is not confused with API/database failure.

Alert routes and phone trees live in the operator's restricted system—not this
repository.

## Related SLOs

See `docs/deployment.md` for beta availability / freshness / outbox targets.
