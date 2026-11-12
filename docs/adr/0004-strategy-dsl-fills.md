# ADR 0004: Restricted strategy DSL and next-session fills

- Status: Accepted
- Date: 2026-11-09

## Decision

Strategies are validated JSON, not arbitrary code. The allowlist covers declared indicators, numeric parameters, boolean comparison/crossover operators, explicit timeframe, and long/flat paper intents. No networking, filesystem, dynamic imports, loops, user functions, or prompt execution is allowed. Compilation is deterministic and versioned.

Signals are evaluated only on closed bars. A signal formed at bar close may fill no earlier than the next eligible session/bar open using the configured price model, fees, slippage, calendar, and liquidity assumptions. Missing next-session data yields no fill. Backtests record all assumptions and reject look-ahead inputs.

## Consequences

Expressiveness is intentionally limited. The same evaluator serves validation, analysis, alerts, and backtests. Live broker execution is out of scope and requires a separate decision and regulatory review.
