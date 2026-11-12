# Operations runbooks

For every event: open an incident record, name an incident commander, preserve
UTC timestamps/evidence, avoid unlogged data edits, communicate known facts
only, and record follow-ups with owners.

Automated checks produce technical evidence. They do not replace a signed data
licence, qualified India regulatory/privacy advice, required notifications, or
real beta-user consent/onboarding. Acceptance records must include date,
environment, release digest, tester, approver, evidence links, result, observed
RTO/RPO where relevant, defects, and retest link.

## Backup restore

Use the dump/restore drill scripts for engineering practice against an
**isolated** database (never a live writer without approved cutover):

```powershell
# PowerShell — requires pg_dump/pg_restore on PATH and DATABASE_URL
.\scripts\backup_restore.ps1 drill
$env:ALLOW_DESTRUCTIVE_RESTORE = "yes"
.\scripts\backup_restore.ps1 restore -DumpFile .\backups\<drill-file>.dump
```

```bash
# Bash
./scripts/backup_restore.sh drill
ALLOW_DESTRUCTIVE_RESTORE=yes ./scripts/backup_restore.sh restore ./backups/<drill-file>.dump
```

Managed Postgres PITR/WAL recovery remains the production path; these scripts
exercise logical dump evidence for acceptance records.

1. Declare scope/RPO/RTO; stop writes for destructive recovery.
2. Provision an isolated database; restore latest base backup plus WAL to target time (or a drill dump via the scripts above).
3. Verify checksums, migration version, row counts, RLS policies, and sampled tenant isolation using non-owner role.
4. Verify object manifests/checksums and reconcile outbox without dispatching.
5. Run smoke tests, approve cutover with two people, rotate credentials if compromise suspected.
6. Monitor and document achieved recovery point/time. Perform quarterly restore tests.

### Backup-restore acceptance

1. Restore a production-shaped encrypted backup and object manifest into an
   isolated environment with external dispatch and provider egress disabled.
2. Record backup timestamp, requested recovery point, actual recovered maximum
   transaction time, elapsed restore time, and missing/corrupt objects.
3. Run migration/version checks, manifest checksums, representative analysis
   reads, non-owner RLS tests, and outbox reconciliation in dry-run mode.
4. Pass only when stated RPO/RTO are met, no integrity error exists, cross-tenant
   probes return no data, and two approvers authorize destruction of the test
   restore. A CI migration test alone is insufficient.

## Market-data vendor outage

1. Alert on contracted freshness; mark provider degraded and stop affected analyses/signals/alerts.
2. Show source/as-of/stale status. Never silently substitute a feed.
3. Contact vendor and capture incident reference. Use fallback only if separately licensed, mapped, and quality-approved.
4. On recovery, ingest to a new dataset version, validate gaps/duplicates, then deliberately re-enable.

### Provider-outage acceptance

1. In staging, use the workspace kill switches to disable publication,
   analysis, AI explanation, and notification dispatch, then simulate timeout,
   rate-limit, stale, malformed, and partial responses.
2. Verify affected requests fail closed; no new dataset is published, no paper
   fill or alert is created, and dashboard provenance retains the last valid
   as-of value rather than claiming freshness.
3. Restore the provider with a new immutable dataset; validate continuity,
   checksum, duplicate sessions, OHLC, attribution, and licence entitlement.
4. Pass only after an operator explicitly re-enables each feature, one
   post-recovery analysis succeeds, audit evidence identifies the transition,
   and no silent unlicensed fallback occurred.

## Data correction

1. Quarantine affected dataset; identify instruments, windows, analyses, backtests, alerts, and paper fills.
2. Preserve original objects/rows. Ingest correction as a new version with `supersedes_id`, reason, checksum, and approver.
3. Recompute only with explicit version links. Notify impacted users if conclusions changed; never rewrite historical evidence.

### Data-correction acceptance

1. Seed a published dataset, analysis, backtest, paper fill, and notification;
   record IDs and checksums. Introduce a known vendor correction.
2. Verify the original version remains byte-identical and queryable for audit,
   while a distinct version/checksum and correction reason are created.
3. Generate an impact report listing every dependent artifact; recompute into
   new records without changing old results or replaying notifications.
4. Pass when lineage points from correction to superseded version, impacted
   conclusions are reviewed, required user notice is approved, and an
   independent checksum comparison confirms no in-place mutation.

## Duplicate alerts

1. Pause the channel/consumer, not all analysis. Find idempotency key and outbox/delivery records.
2. Stop retry loop; determine whether duplicates were queued, dispatched, or provider-generated.
3. Reconcile statuses, add suppression key, resume at low rate, and notify affected users without repeating market claims.

### Duplicate-alert replay acceptance

1. Enqueue one notification with an idempotency key; submit the identical
   request concurrently and again after a simulated worker crash.
2. Capture API responses, outbox rows, provider-send calls, audit events, and
   final status. Repeat with a different workspace using the same key.
3. Pass when one external send occurs per workspace/key, duplicate API responses
   report `created: false`, retries do not create another message, and keys do
   not suppress another tenant. If the provider cannot guarantee idempotency,
   mark the result possibly duplicated and require documented reconciliation.

## Tenant-isolation acceptance

1. Create two users and workspaces with datasets, strategies, analyses,
   notifications, paper orders, watchlists, and audit events.
2. For every workspace route, attempt another workspace's path ID with the
   caller's verified header, then another workspace's header with the caller's
   path ID; test owner, member, publisher, auditor, expired token, and no token.
3. At the database layer, repeat representative `SELECT`, `INSERT`, `UPDATE`,
   `DELETE`, joins, guessed UUIDs, and background-job transactions through the
   non-owner app role with transaction-local tenant context.
4. Pass only when all cross-tenant attempts return 401/403/404 or zero rows,
   create no side effects, generate security/audit evidence, and the app role
   cannot own tables, bypass RLS, or retain tenant settings across pooled
   transactions.

## Prompt-injection acceptance

1. Place adversarial instructions, fake prices, tool requests, secrets, and
   cross-tenant identifiers in every model-visible string field.
2. Use a model stub that returns malformed JSON, extra fields, changed
   disclaimer, unsupported numeric claims, and an exception.
3. Verify the prompt labels facts as untrusted, sends only allowlisted facts,
   exposes no credential/raw provider payload, performs no tool or state-changing
   action, and validates output against the explanation model.
4. Pass when every invalid response produces the deterministic fallback with
   `fallback: true`, fixed disclaimer, recorded prompt/model versions, and no
   alteration of deterministic analysis or risk output.

## Controlled rollback acceptance

1. Before deployment, record application digest, migration version, feature
   flags, queue/outbox depth, data version, and rollback owner; confirm the prior
   image remains deployable.
2. Deploy the candidate with workers/dispatch paused or flags disabled. Trigger
   rollback criteria using a controlled smoke-test failure.
3. Roll back only the application image/configuration to the prior digest.
   Never reverse an applied data migration destructively; use a compatible
   forward fix. Keep suspect datasets quarantined and preserve audit/outbox
   evidence.
4. Re-run health, authentication, tenant isolation, dashboard, analysis,
   next-session paper fill, and dry-run outbox checks before gradually resuming.
5. Pass when recovery completes within the rollback objective, no schema/data
   loss or duplicate dispatch occurs, old and new clients remain compatible,
   and two approvers sign the release/rollback record.

## Privacy request

1. Authenticate requester and jurisdiction; log request/deadline. Do not request secrets or trading credentials.
2. Discover user/profile, memberships, strategies, analyses, paper data, notifications, support, audit, backups, and subprocessors.
3. Export in a secure, expiring channel or delete/anonymize subject to legal/vendor retention. Preserve minimal security/audit records only with documented basis.
4. Propagate to subprocessors; revoke sessions/keys; confirm completion. Backups expire through normal lifecycle, with suppression against restoration.

## Security incident response

1. Triage severity; preserve logs/snapshots; isolate affected credentials, workloads, tenants, providers, or egress.
2. Rotate secrets and revoke sessions; block indicators without destroying evidence.
3. Determine data/users/jurisdictions/time window; involve legal/privacy and vendor contacts.
4. Notify regulators/customers within applicable deadlines using verified scope; do not speculate.
5. Eradicate, restore from trusted artifacts, validate RLS and integrity, monitor recurrence.
6. Complete blameless review within five business days; track control fixes and update this threat model.

Emergency contacts, notification deadlines, backup locations, and vendor escalation paths must be maintained in the operator's restricted system—not this public repository.
