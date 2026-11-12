# Trading terminal architecture

## Runtime flow

1. A provider adapter emits a normalized quote/candle with UTC timestamp,
   source, freshness, and monotonic sequence.
2. REST supplies snapshots/backfill; WebSocket supplies incremental updates.
3. The browser validates payloads, shows connection/freshness state, and treats
   server state as authoritative.
4. A user or agent creates an immutable order intent.
5. The server snapshots quote, authority, positions, balances, limits, and kill
   state, then persists a deterministic risk decision.
6. Approved sandbox intents are claimed by the execution worker with a stable
   idempotency key.
7. Provider acknowledgements and fills become append-only events. Positions,
   balances, and P&L are projections rebuilt from those events.
8. Reconciliation resolves provider/local differences and unknown outcomes.

## Authority boundary

The strategy/LLM/agent layer can propose an intent and explain why. It cannot
submit, cancel, alter limits, grant itself authority, or clear a kill switch.
Those operations belong to deterministic services operating on typed,
workspace-scoped records.

## UI data ownership

- TanStack Query: authenticated REST snapshots and mutations.
- Zustand: ephemeral terminal layout, active instrument/timeframe, ticket
  draft, and stream status.
- WebSocket: quote/candle/order/position/decision deltas carrying sequence.
- Zod: browser-side contract validation.
- Lightweight Charts: OHLC/volume and incremental bars.
- Recharts: portfolio and agent analytics, not market execution state.

## Deployment constraint

Render Free sleeps after inactivity and is not suitable for uninterrupted
market ingestion or strict availability. It is acceptable for a labeled beta
using simulated streams; production market hours require an always-on service,
licensed data, durable workers, monitoring, and tested reconciliation.
