# Privacy notice (draft for counsel review)

> **NOT LEGAL ADVICE.** This document is an engineering handoff draft for
> review by qualified India counsel under applicable law, including the Digital
> Personal Data Protection Act, 2023 (DPDP) and related rules. Do not publish
> or rely on this text for production user-facing notices until counsel
> approves a final version for the operating entity and jurisdictions.

## Who we are

TradePilot is operated by **[operating entity — TBD]**. Contact for privacy
requests: **[privacy contact — TBD]** (see also `docs/legal/support.md`).

## What the product does

TradePilot provides **paper-trading** research tools using **delayed or
end-of-day** market data when a licensed provider is configured. It does **not**
execute live broker orders or hold customer funds. Illustrative demo data may
appear in non-production environments and is not licensed market data.

## Personal data we may process

Depending on configuration and beta scope:

- Account identifiers (for example email), authentication session metadata
- Workspace membership and role
- User-provided strategy names/settings, watchlists, and paper-trade records
- Notification destination identifiers (for example Telegram chat IDs) when
  the user enables alerts
- Support correspondence and limited security/audit logs
- Technical logs (IP, user agent, request identifiers) for security and
  reliability

We do **not** ask for brokerage passwords, fund custody credentials, or live
trading API keys for the MVP.

## Purposes

- Provide and secure the service
- Operate paper portfolios, analyses, and optional alerts
- Diagnose incidents and prevent abuse
- Meet legal obligations and respond to authenticated privacy requests

## Legal basis / consent (counsel to finalize)

Counsel must map purposes to DPDP consent or other lawful bases, age
eligibility, and any cross-border transfer mechanisms before launch.

## Market data and third parties

Licensed market-data vendors, infrastructure hosts (for example database,
object storage, hosting), error monitoring (if `SENTRY_DSN` is enabled), and
messaging providers (Telegram) may process limited data as subprocessors.
Vendor contracts and DPDP-compliant terms are **external blockers** and must
exist before production personal-data processing.

## Retention

Retention schedules are **TBD by counsel** and must align with the market-data
licence, security/audit needs, and deletion/backup lifecycle. Backups expire
through normal lifecycle; restored copies must respect suppression flags.

## Your requests

Authenticated users may request access, correction, or deletion subject to
legal exceptions (security/audit preservation). Use the support contact. Do
not send secrets or trading credentials in privacy tickets.

## Children

Not intended for minors. Exact age gate: **TBD by counsel**.

## Changes

Material changes will be notified through the product or email once a
production notice process is approved.

## Status

**Draft — blocked on India counsel DPDP/SEBI review** (`docs/release-gate.md`).
