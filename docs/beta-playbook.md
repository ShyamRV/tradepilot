# Controlled beta playbook

## Entry, cohort, and boundaries

Start only after the release gate is approved. Recruit 5–10 active traders across intended workflows; onboarding actual users is an external action. Use invitation-only accounts, one licensed market, delayed/EOD data, paper trading, support hours, quotas, and an explicit end date. Exclude minors, restricted territories, live execution, custody, shared credentials, performance promises, and public redistribution.

Before access: interview workflow; verify eligibility and consent; explain delay, limitations, privacy, incident contact, and deletion path; configure least privilege; record preferred instruments/timeframes and success criteria; teach source/as-of and paper labels.

## Weekly operation

- Daily: provider freshness/quality, failed analyses, outbox/duplicate alerts, access anomalies, costs.
- Weekly: 20-minute user interview plus structured survey; review a sample analysis against its evidence; triage issues by safety, correctness, reliability, usability, then feature demand.
- Never use profitable simulated trades as validation. Pause affected features on critical data, tenant, risk, or misleading-output defects.

## Metrics

Measure per cohort and week with privacy-minimized event names:

- Activation: invited → consented → workspace configured → first validated strategy → first completed analysis.
- Engagement: weekly active users, analyses/user, 4-week retention, strategy revisions, paper-trade reviews.
- Utility: task time saved, explanation usefulness (1–5), alert useful/noisy ratio, willingness-to-pay interview result.
- Correctness/safety: critical data errors (target 0), unsupported numeric claims (0), cross-tenant exposure (0), stale-data suppressions, strategy validation failures.
- Reliability: analysis completion ≥98%, p95 duration, freshness within licence delay +10 min, alert dispatch ≥99%, duplicates <0.1%.
- Economics: vendor/LLM/infrastructure cost per active user; support minutes per user.

Define event properties without raw prompts, strategy text, prices, or emails: `event_name`, pseudonymous `user_id`, `workspace_id`, `occurred_at`, `release`, `provider`, `timeframe`, `outcome`, `latency_bucket`, `error_code`.

## Feedback and decisions

Store interview notes separately with consent and restricted access. Link feedback to workflow, severity, frequency, evidence, and suggested outcome—not requested implementation. Publish a weekly decision log: continue, change, pause, or stop; owner; due date; metric expected to move.

Exit to broader availability only if four consecutive weeks meet safety/reliability targets, at least 5 users return in week four, evidence shows repeated utility, unit costs are bounded, and release approvers sign again. Otherwise narrow scope or stop and notify participants.
