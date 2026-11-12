# Autonomous terminal backend

This slice is intentionally sandbox-only. `PAPER_TRADING` defaults to
`true`; `AUTONOMOUS_TRADING_ENABLED` and `LIVE_EXECUTION_ENABLED` default to
`false`. Startup rejects a non-sandbox broker, live execution, or disabling
paper trading.

## Ports and adapters

- `MarketDataProvider` exposes typed `Quote` values.
- `BrokerGateway` accepts typed `OrderRequest` values and reports whether it
  is a sandbox.
- `SimulatedMarketDataProvider` produces deterministic seeded price movement
  and a configurable bid/ask spread.
- `SandboxBroker` applies configured adverse slippage and caps each fill,
  producing realistic partial fills.

All prices, values, fees, limits, and P&L use `Decimal`. Timestamps are stored
as timezone-aware UTC values.

## Controls

Agent creation is allowed while autonomy is disabled so a configuration can
be reviewed. Starting or resuming an agent requires
`AUTONOMOUS_TRADING_ENABLED=true`. Every create/control action, risk decision,
and order is appended to the existing audit repository. A killed agent cannot
be restarted.

Pretrade checks are deterministic and report all failures in stable order:
daily loss, open orders, order value, per-symbol position, cash, and inventory.
Agent orders additionally require a running agent, an allowlisted symbol, and
the configured capital and daily-loss guardrails.

## Persistence

The runtime stores agents, risk decisions, and sandbox orders through the
existing tenant-scoped `Repository`, so in-memory, SQLite, and PostgreSQL
deployments work without an adapter change. Migration
`0003_autonomous_terminal.sql` defines normalized PostgreSQL projections for a
future repository adapter; it is additive and does not alter Neon/Render
runtime tables.

## API

- `GET /v1/workspaces/{workspace}/market/quotes/{symbol}`
- `WS /v1/workspaces/{workspace}/market/stream/{symbol}?token=...`
- `POST|GET /v1/workspaces/{workspace}/sandbox/orders`
- `POST|GET /v1/workspaces/{workspace}/agents`
- `POST /v1/workspaces/{workspace}/agents/{agent}/control`

The WebSocket token is a short-lived application session token. Production
deployments should move it to a secure same-site cookie or a one-use ticket to
avoid query-string logging.
