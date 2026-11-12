# Deployment guide

## Development

Use `compose.yaml` for loopback-only PostgreSQL and MinIO. Copy `.env.example` to `.env`, replace defaults, start services, apply migrations, then run contract validation. Local data is disposable; do not load production data or vendor feeds without explicit non-production rights.

## Production packaging

- Build the API/worker image with `Dockerfile` (default CMD: uvicorn; worker override: `python -m apps.worker.main`).
- Local production-shaped stack: `docker compose -f docker-compose.prod.yaml up --build`.
- Hosted blueprints: `railway.toml` (Railway) and `render.yaml` (Render). Keep the web app on Vercel and set `NEXT_PUBLIC_API_URL` to the public HTTPS API origin; allow that origin in `TRADEPILOT_CORS_ORIGINS`.
- Backup dump/restore drill: `scripts/backup_restore.ps1` / `scripts/backup_restore.sh` (see `docs/runbooks.md`).
- Monitoring: structured logs, `/health`, `/ready`, `SENTRY_DSN` stub — `docs/monitoring.md`.
- Developer handoff / external blockers: `docs/DEVELOPER_HANDOFF.md`.

## Production topology

- Managed PostgreSQL 16 with point-in-time recovery, encrypted storage, private networking, separate owner/app/backup roles, connection pooling in transaction mode.
- Private S3-compatible storage with versioning, encryption, blocked public access, lifecycle policy compatible with vendor retention terms.
- API and worker as separate processes from the same immutable image/revision; bounded queues and transactional outbox.
- Managed secret store and workload identities; no long-lived secrets in images, environment files, CI logs, or model prompts.
- TLS at ingress, WAF/rate limits, egress allowlist, centralized redacted logs, metrics, traces, alerts, and UTC clocks.

## Release procedure

1. Complete `docs/release-gate.md`; attach vendor/legal evidence outside the repository.
2. Build once; generate SBOM, scan, sign, and promote the same digest.
3. Back up and test migration on a recent sanitized snapshot.
4. Apply backward-compatible migrations with the owner role; verify RLS is forced and app role cannot bypass it.
5. Deploy workers paused, then API; run health, tenant-isolation, stale-data, and object-access smoke tests.
6. Resume ingestion/workers gradually; verify freshness, outbox lag, errors, and costs.
7. Record release, schema, model, strategy-engine, and dataset-adapter versions.

Rollback application images immediately for runtime regressions. Database changes use forward fixes; do not destructively roll back a migration containing user data. Quarantine suspect datasets rather than deleting lineage.

## SLOs and alerts

Initial beta targets: API availability 99.5%; analysis completion ≥98%; alert dispatch success ≥99% excluding recipient/provider rejection; zero cross-tenant disclosures; data freshness within contracted delay plus 10 minutes. Page on tenant/security events, failed backups, provider freshness breach, outbox age >5 minutes, or sustained error rate >5%.

## External dependencies

A licensed market-data agreement, qualified legal/regulatory review for intended markets and claims, production provider credentials, and actual user onboarding are external actions. Deployment readiness does not satisfy them.
