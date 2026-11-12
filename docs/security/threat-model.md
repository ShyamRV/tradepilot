# Threat model

## Scope and trust boundaries

Assets: identities, workspace data, licensed market data, provider/LLM/Telegram secrets, strategy IP, audit evidence, paper ledgers, and availability. Boundaries are browser/API, API/database, job queue/worker, provider adapters, object storage, LLM provider, and notification providers. Live execution and customer funds are explicitly out of scope.

## Principal threats and controls

| Threat | Impact | Required controls |
|---|---|---|
| Broken tenant authorization / IDOR | Cross-customer disclosure | Membership checks, RLS, opaque IDs, negative tenant tests |
| SQL injection or unsafe filters | Data compromise | Parameterized queries, allowlisted sort/filter fields, least-privilege DB role |
| Prompt injection / tool abuse | Leakage or fabricated action | Treat prompts as data, minimal context, allowlisted scoped tools, output schemas |
| Secret leakage to logs/models | Account/vendor compromise | Secret manager, redaction, no secrets in prompts, rotation and egress controls |
| Malicious strategy definition | Code execution/DoS | JSON DSL only, limits on depth/window/cost, no arbitrary code |
| Poisoned/stale/vendor data | False analysis/alerts | Immutable versions, checksums, quality gates, provenance, stale fail-closed |
| Look-ahead or dataset substitution | Misleading backtests | Closed bars, next-session fills, pinned versions, immutable assumptions |
| Duplicate jobs/webhooks | Duplicate alerts/trades | Idempotency keys, unique constraints, outbox, replay timestamp/signature |
| Object-store exposure | Licensed/user data leak | Private buckets, short-lived signed URLs, encryption, deny public ACLs |
| Account takeover | Unauthorized access | Strong password hashing, MFA-ready auth, session revocation, rate limiting |
| Insider/support misuse | Privacy breach | No standing access, approval, reason code, audit log, periodic review |
| Dependency/build compromise | Service compromise | Locked dependencies, CI scanning, pinned images, provenance and rollback |
| Resource exhaustion | Outage/cost spike | Quotas, bounded backtests, timeouts, queues, per-tenant rate limits |

## Abuse cases

- User asks the assistant to reveal another workspace: authorization occurs before retrieval; model never selects tenant.
- User encodes instructions in news/strategy text: content is quoted and cannot grant tools.
- Provider replays/corrects bars: deduplicate ingestion; correction creates a superseding dataset and impact report.
- Worker retries notification: idempotency key prevents a second external send where the channel supports it; otherwise record possible duplicate.
- Staff exports data “for debugging”: production export is denied without approved, audited break-glass procedure.

## Security verification

Before release: threat-owner review; cross-tenant integration tests; restore test; secret and dependency scans; webhook replay test; object-store public-access check; prompt-injection suite; stale/malformed data tests; incident tabletop. Reassess after new vendors, jurisdictions, data classes, privileged paths, or any live-execution proposal.

Residual risks and exceptions require named owner, expiry, compensating control, and written acceptance.
