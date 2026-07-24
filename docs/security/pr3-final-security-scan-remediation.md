# PR #3 final security scan remediation

## Scope

The sealed diff scan of revision `783eea7ff4018d0d9861d06ed2d2281ef325bf69`
reported two Medium and four Low findings across 115 reviewed worklist rows.
This document records the sanitized remediation contract; the detailed scan
report and exploit-oriented artifacts are intentionally not copied into the
repository.

PR #3 remains a synthetic/demo validation branch. This work does not authorize
production use, real patient data, or human usability claims.

## Remediated root causes

| Finding | Root cause | Enforced invariant | Regression proof |
| --- | --- | --- | --- |
| Anonymous rejected-session audit amplification | every equivalent anonymous probe created an independent durable row | five-minute, database-atomic aggregation by sanitized action/reason/method/route bucket; 90-day cleanup applies only to aggregated anonymous probe rows | 40 equivalent requests preserve 40 occurrences in fewer than four rows; PostgreSQL parallel writer test |
| Unscoped direct audit references | caller-selected `AuditLog` IDs were persisted without loading the referenced record | exact record load followed by clinic, institution-clinical, or explicit system-security authorization | missing, foreign clinic, foreign institution, and system permission denial tests |
| Unresolved appointment room | nullable room clinic provenance passed create and patch checks | room clinic must exactly equal the active clinic; the central creation service also requires an explicit clinic | create, patch, package, and activity resource tests |
| Global latest audit lookup | the just-created access event was replaced by a global highest-ID query | `audit()` returns the exact ORM instance it added and callers return that instance after flush | later-ID regression plus PostgreSQL interleaving test |
| Unresolved provider ownership | a provider without a clinic was treated as institution-compatible | unresolved provider provenance is denied for clinical ownership, task assignment, package activity, and journey activity assignment | same-institution positive controls and unresolved/foreign denial tests |
| Silently skipped unresolved evidence | reviewed evidence with no institution did not produce a readiness signal | unresolved evidence never contributes positively and creates an explicit `unresolved_evidence_provenance` physician-review limitation | unresolved-only and valid-plus-unresolved projection tests |

## Audit aggregation privacy and retention

The aggregation key is a server-side SHA-256 digest of a bounded tuple:

```text
action | rejection reason | HTTP method | normalized route template | five-minute UTC bucket
```

It excludes raw IP addresses, cookies, session identifiers, authorization and
CSRF headers, user agents, request bodies, patient identity, and clinical
content. The first request creates a durable signal. Concurrent equivalent
requests atomically increment `occurrence_count` and `last_seen_at` through
PostgreSQL `ON CONFLICT`; different reasons, routes, methods, or windows remain
separate. Aggregated anonymous probe rows older than 90 days are removed during
the next aggregated write. Non-aggregated security and business audit records
are not affected by this cleanup.

## Migration

Revision `0067_audit_aggregation` additively introduces:

- `audit_logs.occurrence_count`;
- `audit_logs.first_seen_at`;
- `audit_logs.last_seen_at`;
- `audit_logs.aggregation_key`;
- one index for cleanup and one unique constraint for atomic aggregation.

The empty-database upgrade, `0067 -> 0066` downgrade, and `0066 -> 0067`
re-upgrade complete successfully. Historical metadata drift remains separately
classified; no `0067` object appears in the unclassified comparison output.

## Validation evidence

Measured locally on 24 July 2026:

- focused owning-module suite: `120 passed, 1 skipped`;
- focused remediation checks after final adjustments: passed;
- PostgreSQL remediation concurrency suite: `2 passed`;
- empty PostgreSQL migration and downgrade/re-upgrade cycle: passed;
- Python compile and `git diff --check`: passed.

Full backend, frontend, browser, Compose, CI, independent review, and the new
sealed Codex Security scan are closure gates and must be recorded here only
after they are actually executed.

## Current decision

Remediation is locally implemented and focused checks pass. PR #3 remains
Draft until the full local gate, current-head CI, independent remediation
review, merge into the PR #3 integration branch, and a new sealed full diff
scan all pass.
