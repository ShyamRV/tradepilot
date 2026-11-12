# ADR 0007: Sandbox-only autonomous execution

## Status

Accepted for the beta implementation. This decision does not authorize
live-money trading.

## Context

TradePilot needs a realistic trading terminal and autonomous-agent workflow
without allowing an LLM, strategy, or UI bug to reach a production broker
account. Broker APIs differ in order semantics, sandbox fidelity, account
metadata, retry behavior, and market-data rights.

## Decision

- Market data and execution use provider-neutral `MarketDataProvider` and
  `BrokerGateway` ports.
- The first adapters are deterministic simulated providers. A remote adapter
  may be enabled only for a documented broker sandbox/testnet.
- `PAPER_TRADING=true` and `BROKER_EXECUTION_ENABLED=false` are defaults.
  Enabling sandbox execution also requires `BROKER_ENVIRONMENT=sandbox`.
- Adapters must reject production hosts and verify sandbox account metadata.
- Agents create immutable order intents. Only deterministic policy and risk
  services may authorize submission; LLM output cannot call a gateway.
- Every request, quote snapshot, risk result, authority decision, provider
  acknowledgement, fill, cancel, rejection, reconciliation result, pause, and
  kill is append-only and workspace scoped.
- Unknown submission outcomes reconcile before retry. Idempotency keys are
  stable across retries.
- Global, provider, workspace, user, and agent controls fail closed. Emergency
  kill blocks new submissions immediately; already-submitted orders are
  reconciled and cancelled where supported.
- Money uses Decimal, storage timestamps use UTC, and the UI displays IST.

## Consequences

The terminal can behave like a real trading product while using simulated
funds. Licensed real-time NSE data, a selected broker sandbox, provider
credentials, and legal review remain external gates. Live-money execution
requires a separate ADR, threat model, migration, legal approval, audited
feature flag, and per-user confirmation; it is unreachable under this ADR.
