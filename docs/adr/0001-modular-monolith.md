# ADR 0001: Modular monolith for the MVP

- Status: Accepted
- Date: 2026-11-09

## Context

A small team needs clear market-data, strategy, risk, paper-trading, notification, and AI boundaries without distributed-system overhead.

## Decision

Deploy one API/worker codebase and one PostgreSQL cluster. Each module owns its domain service, tables, commands/events, and public interfaces; imports may point inward to shared primitives but not into another module's internals. Cross-module side effects use a transactional outbox. CPU-heavy backtests may run as isolated workers while remaining in the same logical application. Object storage holds immutable dataset objects and large artifacts.

## Consequences

One release and transaction boundary simplifies operation and consistency. Module ownership and architecture tests are mandatory to avoid a “big ball of mud.” Extraction to a service is justified only by measured scaling, security, or team-boundary needs.
