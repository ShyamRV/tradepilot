# TradePilot

Production-oriented foundation for a multi-tenant trading intelligence MVP. TradePilot analyses licensed delayed/end-of-day market data, evaluates restricted strategies, explains deterministic outputs, and records paper trades. It does **not** place live orders, hold funds, or promise returns.

## Prerequisites

- Python 3.11 or newer for the API and tests.
- Node.js 22 and npm for the web dashboard.
- Docker with Compose v2 only when running PostgreSQL and MinIO locally.

## Backend

From the repository root, create an environment and install the package:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
```

Run all backend tests:

```powershell
python -m pytest
```

Start the development API on `http://127.0.0.1:8000`:

```powershell
python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API documentation is at `http://127.0.0.1:8000/docs`. The
default `create_app()` uses in-memory accounts, opaque sessions, workspaces,
datasets, and paper ledgers. Everything disappears on process restart. Register,
log in, create a workspace, then send both `Authorization: Bearer <token>` and
the verified `X-Workspace-ID` header to workspace routes. This is demo/test
behavior, not a production identity or persistence configuration.

## Web dashboard

Install and run from the repository root:

```powershell
npm install
npm run typecheck
npm run dev
```

Open `http://localhost:3000`. With `NEXT_PUBLIC_API_URL` unset, the page
intentionally renders the static illustrative NSE/EOD demo in
`apps/web/lib/api.ts`; its prices, signals, portfolio, and performance are not
live or user results. If `NEXT_PUBLIC_API_URL` is set, the web app provides
registration/login and workspace selection, keeps the opaque session only in
`sessionStorage`, and sends the required Bearer session and verified
`X-Workspace-ID` header to `/api/dashboard`. API-configured errors are shown
explicitly and never replaced with fabricated demo data.

Production build commands:

```powershell
npm run build
npm run start --workspace=@tradepilot/web
```

## Optional local infrastructure

Copy `.env.example` to `.env`, replace all placeholders, then:

```powershell
docker compose up -d
docker compose ps
Get-Content migrations/0001_initial.sql | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U tradepilot -d tradepilot
```

PostgreSQL is exposed on `127.0.0.1:5432`; MinIO API/console on
`127.0.0.1:9000` and `127.0.0.1:9001`. The current default API does **not**
connect to these services; they are the persistence target for a production
repository adapter.

Database adapters must authenticate membership, start a transaction, and set:

```sql
SET LOCAL app.user_id = 'user-uuid';
SET LOCAL app.workspace_id = 'workspace-uuid';
```

The deployed application role must not own tables or have `BYPASSRLS`.

## Architecture and contracts

- Decisions: `docs/adr/`
- Threat model: `docs/security/threat-model.md`
- HTTP contract: `docs/api/openapi.yaml`
- JSON contracts: `schemas/`
- Database and RLS: `migrations/`
- Deployment: `docs/deployment.md`
- Runbooks: `docs/runbooks.md`
- Release gate: `docs/release-gate.md`
- Controlled beta: `docs/beta-playbook.md`

Validate machine-readable contracts:

```powershell
python -m pip install -e . -r scripts/validation-requirements.txt
python scripts/validate_contracts.py
```

The validator checks each JSON Schema, resolves and validates OpenAPI, and
compares documented path/method pairs with the FastAPI route table.

## External prerequisites

Automated tests can produce engineering evidence; they cannot grant legal rights
or recruit users. Production release remains blocked on a signed licensed
market-data vendor agreement, qualified India regulatory/privacy review for the
actual product and claims, and real controlled-beta onboarding by authorized
people.

## Security reporting

Do not open public issues containing credentials, user data, or vulnerabilities. Follow the incident process in `docs/runbooks.md` and route security reports to the private security contact configured by the operator.
