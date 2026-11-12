# Terms of use (draft for counsel review)

> **NOT LEGAL ADVICE.** This document is an engineering handoff draft for
> review by qualified India counsel (including SEBI applicability,
> research/adviser boundaries, and marketing claims). Do not publish as binding
> terms until counsel approves a final version for the operating entity and
> intended jurisdictions.

## Service description

TradePilot is a **paper-trading** and research MVP. Features may include
strategy evaluation, deterministic analysis explanations, and optional
notifications. The service:

- Uses **delayed and/or end-of-day** market data when a **licensed** provider is
  configured
- Records **simulated / paper** fills only
- Does **not** place live orders, provide custody, process withdrawals, or
  guarantee profits

Demo or fixture prices shown without a licensed feed are **illustrative only**
and must not be treated as redistributable exchange data.

## No investment advice

Unless counsel expressly reclassifies the product after review, outputs are
**informational / educational** and **not** investment advice, a research
report under applicable securities regulations, or a solicitation to buy or
sell securities. You remain solely responsible for any trading decisions made
outside the paper environment.

## Eligibility

Beta access is invitation-only. Users must meet age and territory rules set by
counsel. Restricted territories and regulated-user classes must be enforced
before launch.

## Accounts and acceptable use

- Provide accurate registration information; do not share credentials
- Do not attempt cross-tenant access, scraping, reverse engineering of
  licensed data feeds, or abuse of rate limits
- Do not redistribute market data or derived vendor content except as allowed
  by the data licence

## Data, delay, and accuracy

Market data may be delayed (for example fifteen minutes or end-of-day). Labels
for source and as-of time are part of the product contract with users. Past
paper performance does **not** predict future results. Analyses may be wrong,
incomplete, or unavailable during vendor outages.

## Alerts

Telegram or other alerts, when enabled, may be delayed, duplicated, or dropped.
Alerts are not a substitute for your own monitoring and are subject to channel
provider terms.

## Quotas and suspension

We may apply quotas, feature kill switches, or suspend access to protect
tenants, honour vendor limits, or investigate abuse.

## Intellectual property

The software, branding, and non-vendor content remain the operator's property.
Licensed market data remains subject to vendor/exchange terms.

## Disclaimers and liability

Counsel must finalize warranty disclaimers, liability caps, indemnities, and
governing law. Until then, the software is provided for controlled beta /
evaluation only.

## Privacy

Personal data handling is described in the privacy notice draft
(`docs/legal/privacy.md`) and remains subject to counsel approval.

## Contact

Support and complaints: see `docs/legal/support.md`.

## Status

**Draft — blocked on India counsel SEBI/DPDP and claims-language review**
(`docs/release-gate.md`).
