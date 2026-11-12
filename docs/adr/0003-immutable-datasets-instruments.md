# ADR 0003: Immutable datasets and internal instrument identity

- Status: Accepted
- Date: 2026-11-09

## Decision

Use a stable UUID as TradePilot's instrument identity. Provider symbols are time-bounded aliases, never primary keys; aliases include provider, venue, vendor ID, valid interval, currency, and multiplier. Corporate actions and symbol changes create mappings, not identity rewrites.

An ingestion run creates an immutable dataset version with a manifest, provider entitlement reference, retrieval window, checksum, schema version, and quality status. Candle rows reference the version and are insert-only. Corrections create a superseding version and preserve lineage. Analyses, backtests, and paper fills pin exact dataset and strategy versions.

## Consequences

Results are reproducible and corrections auditable. Storage grows, so contract-compatible lifecycle rules are required. “Latest” is resolved at query time and never mutates historical evidence.
