# Developer handoff

TradePilot is a multi-tenant, paper-trading intelligence MVP. It analyses
**licensed delayed / end-of-day** market data, evaluates restricted strategies,
explains deterministic outputs, and records **paper** trades. It does **not**
place live broker orders, hold funds, or promise returns.

This document separates **implemented engineering** from **external blockers**
that automation and this repository cannot close.

## Implemented in-repo

| Area | Status |
| --- | --- |
| FastAPI modular monolith (`packages/tradepilot`, `apps/api`) | Auth, workspaces, datasets, strategies, analysis, paper fills, outbox enqueue, rate limit + security headers, `/health`, `/ready` |
| Durable runtime | `DATABASE_URL` → Postgres (`psycopg`); `TRADEPILOT_DB_PATH` → SQLite; otherwise in-memory (non-production) |
| Worker entry (`apps/worker`) | Outbox dispatch loop sharing `build_runtime()`; needs owned Telegram token for live sends |
| Web dashboard (`apps/web`) | Next.js UI; demo mode without `NEXT_PUBLIC_API_URL`, live API mode when set |
| Postgres schema (`migrations/`) | Initial SQL with RLS-oriented tenancy model (alongside runtime auto-schema for MVP adapters) |
| Local infra (`compose.yaml`) | Loopback Postgres + MinIO |
| Production packaging | `Dockerfile`, `docker-compose.prod.yaml`, `railway.toml`, `render.yaml` |
| Backup drill scripts | `scripts/backup_restore.ps1`, `scripts/backup_restore.sh` + runbook |
| Contracts / security docs | OpenAPI, ADRs, threat model, release gate, beta playbook |
| Legal drafts | `docs/legal/*` — **counsel-review drafts only** |
| Monitoring stubs | Structured JSON logs, `/health` + `/ready`, `SENTRY_DSN` env stub, uptime notes in `docs/monitoring.md` |

### Quick start for a receiving developer

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
python -m pytest
python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
npm install
npm run typecheck
npm run dev
```

Production-shaped API stack:

```powershell
copy .env.example .env
# edit .env — set POSTGRES_PASSWORD
docker compose -f docker-compose.prod.yaml up --build -d
```

Hosted API (forever-free on Render): see `docs/render-free.md` — Render Free
web service (`render.yaml` + `scripts/render_start.sh`) + Neon Free Postgres.
Oracle Always Free alternative: `docs/oracle-always-free.md`. Point Vercel
`NEXT_PUBLIC_API_URL` at the public HTTPS API origin after deploy, and mirror
that origin in `TRADEPILOT_CORS_ORIGINS`.

## External blockers (cannot be closed by code alone)

| Blocker | Why it blocks real beta | Owner action |
| --- | --- | --- |
| **Licensed NSE delayed/EOD data** | Demo/fixture prices are illustrative and not redistributable exchange data. No signed vendor contract means production ingestion/display/alerts are not entitled. | Sign vendor agreement covering environments, territory, storage, derived data, alerts, paper trading, DR copies; load credentials via secrets manager only. |
| **India counsel — SEBI / DPDP** | Personalized analytics/alerts may have adviser/research boundaries; DPDP obligations, retention, subprocessors, consent, and claims language need qualified advice. | Engage India counsel; convert written advice into product controls and approved terms/privacy/support text. |
| **Real tester onboarding** | No consented 5–10 person cohort yet. CI and demo screens are not user validation. | Recruit under `docs/beta-playbook.md`; record consent, eligibility, workspace config, feedback. |
| **Telegram token ownership** | Outbox + worker code exist; production bot token, chat binding, and operator ownership are not live. | Create/own bot under the operating entity; store `TELEGRAM_BOT_TOKEN` in secrets manager; enable worker dispatch with kill switches. |
| **Secrets manager** | `.env` is local-only. Production must not keep long-lived secrets in images, git, or CI logs. | Provision managed secrets (Railway/Render/AWS/GCP/Vault); inject at runtime; rotate on incident. |

Additional production follow-ups (engineering):

- Enable Sentry when `SENTRY_DSN` is provisioned (`docs/monitoring.md`); install SDK in a follow-up.
- Configure external uptime checks on `/health` and `/ready`.
- Run the backup/restore drill and file acceptance evidence (`docs/runbooks.md`).
- Align runtime Postgres adapter with full `migrations/` RLS owner/app roles before broad beta.
- Connect frontend production env (`NEXT_PUBLIC_API_URL`) only after API HTTPS and CORS match.

## Explicitly out of MVP

- Live broker trading / custody / withdrawals
- Real-time (non-delayed) prices
- Guaranteed profits or prediction claims
- Unlicensed scraping of exchange data

## Acceptance reminder

Passing CI, Compose healthchecks, or a local demo **does not** satisfy the
external blockers in `docs/release-gate.md`. Release remains blocked until
licensed data, counsel review, and real tester onboarding evidence exist.
