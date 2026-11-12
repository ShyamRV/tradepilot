# ADR 0002: Licensed delayed/end-of-day market data

- Status: Accepted
- Date: 2026-11-09

## Context

“Available from an API” does not imply storage, display, derived-work, or redistribution rights. Real-time entitlements add cost and exchange obligations.

## Decision

The MVP supports only contractually licensed delayed or end-of-day data. Every observation records provider, vendor symbol, exchange, event time, received time, dataset version, quality state, and delay class. UI/API responses display source, as-of time, and delay. Stale, incomplete, quarantined, or out-of-entitlement data cannot produce an actionable setup. Adapters enforce provider-specific retention/export controls.

Provider enablement requires a signed contract and completed release gate covering territory, user class, storage, derived data, display, redistribution, audit, attribution, deletion, and outage terms.

## Consequences

No “real-time” claims or silent fallback to scraped/free feeds. Features may be unavailable by market or territory. Vendor contracting remains an external action and is not completed by this repository.
