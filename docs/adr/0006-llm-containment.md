# ADR 0006: LLM containment

- Status: Accepted
- Date: 2026-11-09

## Decision

LLMs explain or translate; deterministic code retrieves data, calculates indicators/risk, evaluates strategies, authorizes access, and dispatches alerts. The model receives a minimal, schema-validated envelope with pseudonymous IDs and cited facts—never credentials, raw provider payloads, unrestricted documents, or cross-tenant context.

Tool access is allowlisted, read-only by default, workspace-scoped, rate-limited, and schema-validated on input/output. Generated strategy JSON must validate and receive user confirmation. Prompt content is untrusted data. Model output is labelled, checked for unsupported numeric claims, linked to evidence, and cannot change risk decisions. Providers require retention/training controls and regional/privacy review.

## Consequences

Model failures degrade to deterministic output rather than blocking calculations. Prompts, model/version, evidence IDs, and validation outcomes are auditable with sensitive content redacted. Automated live trading remains impossible.
