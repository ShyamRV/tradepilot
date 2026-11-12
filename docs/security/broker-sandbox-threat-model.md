# Broker sandbox and autonomous-agent threat model

## Scope and boundaries

This model covers simulated market streams, broker sandbox accounts, order
intents, deterministic risk, autonomous-agent decisions, execution workers,
reconciliation, and terminal WebSockets. Production broker accounts, customer
funds, custody, withdrawals, and live-money orders remain prohibited.

## Required controls

| Threat | Required control |
| --- | --- |
| Sandbox credential reaches browser/model/log | Server-side secret reference, redaction, scoped credential, rotation |
| Adapter points to production | Sandbox hostname allowlist, production denylist, provider environment verification |
| LLM bypasses policy | Typed proposal only; deterministic authority, risk, and kill checks |
| Duplicate submit after timeout | Stable idempotency key; unknown state; reconcile before retry |
| Stale or manipulated quote | Sequence/freshness validation, maximum age/deviation, fail closed |
| Cross-workspace stream/order access | Session plus membership on REST and WebSocket subscribe; tenant tests |
| Partial fill causes excess position | Fill-level ledger, reservation accounting, continuous risk reconciliation |
| Kill switch races queued work | Controls read in the submitting transaction and immediately before provider call |
| Stream replay or reordering | Monotonic sequence, snapshot/backfill, gap detection, reconnect |
| Agent exceeds delegated authority | Versioned capital/universe/schedule limits persisted with each decision |
| Audit failure hides an action | Intent, risk, audit, and outbox write atomically before external submission |
| Malicious provider payload | Strict schemas, bounded fields, normalized enums/errors, no pickle at trust boundary |

## Failure behavior

- Missing, stale, ambiguous, or unauthorized input denies submission.
- A provider timeout after transmission becomes `unknown`, never an automatic
  second submit.
- Emergency kill denies new work and requests cancellation for open sandbox
  orders; reconciliation remains active.
- WebSocket loss never changes authoritative state. Clients fetch a REST
  snapshot and resume from the last accepted sequence.

## Release evidence

Release evidence must include sandbox-host denial, idempotent replay,
timeout/unknown reconciliation, partial fill then cancel, stale quote,
daily-loss rejection, tenant isolation, kill races, malicious-LLM attempts,
and append-only trace tests. Provider terms and India legal review are human
gates even when all automated tests pass.
