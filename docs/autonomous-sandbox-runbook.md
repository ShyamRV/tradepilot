# Autonomous sandbox operations

## Preconditions

- `PAPER_TRADING=true`
- `BROKER_EXECUTION_ENABLED=true` only in an approved sandbox environment
- `BROKER_ENVIRONMENT=sandbox`
- Production broker hosts/accounts are denied
- Market stream is simulated or covered by a signed data agreement
- `/ready` is healthy and database backups have been tested

## Emergency kill

1. Activate the global execution kill switch.
2. Pause all agents and stop new order-intent claiming.
3. Request cancellation of cancellable sandbox orders.
4. Keep reconciliation running until every submitted/unknown order is resolved.
5. Preserve audit and provider responses; do not delete or rewrite events.
6. Notify the named operator and record the incident timeline.

The kill switch must fail closed. It must not stop reconciliation or hide
already-submitted orders.

## Unknown broker outcome

1. Mark the order `unknown`; do not resubmit.
2. Query by provider order ID and idempotency/client reference.
3. Reconcile acknowledgements, fills, and open-order state.
4. Escalate after the bounded retry window.
5. Resume automation only after authoritative state is known.

## Stale market stream

1. Mark the UI and server subscription stale.
2. Reject new market-dependent order previews/submissions.
3. Reconnect, verify sequence continuity, and REST-backfill gaps.
4. Require a fresh quote inside the configured maximum age before resuming.

## Agent incident

Pause the agent first, then inspect the immutable decision trace: strategy and
dataset versions, signal evidence, LLM provider/model/prompt version,
deterministic risk checks, authority version, kill-state observation, order
intent, and execution events. An LLM explanation is never proof that an order
was authorized.
