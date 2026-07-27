# PR #3 Sixth Security Rescan Remediation

## Scan context

- Scanned head prefix: `f50cc71`
- Coverage: `124/124`
- Reportable findings: `3 Medium / P2`
- Suppressed: `2`
- Not applicable: `1`
- Manifest and artifact hashes: verified

## Remediation

### Evidence-based legacy classification

Migration `0069_legacy_document_trust` adds separate classification reviewer
provenance. It backfills that provenance only from complete existing medical
review metadata and demotes every `clinical` record that cannot also prove:

- an active medical reviewer;
- a review timestamp;
- consistent clinic/institution provenance; and
- an active Patient–Clinic association.

The migration does not delete documents, alter source content, manufacture
associations or create synthetic audit events. Its downgrade removes the new
schema fields but intentionally does not re-promote unsafe classifications.

### Server-owned authoritative access auditing

The direct `/api/audit/access-events` compatibility endpoint can no longer
write any authoritative sensitive-access action. It returns a controlled
conflict before object resolution and before the audit writer is called,
regardless of whether the client omits, repeats or changes `interaction_id`.
The OpenAPI operation is marked deprecated.

Existing authorized resource routes remain the owners of their access,
download, print and mutation audit events. The internal collection-view event
for the audit list remains server-only.

The patient detail, journey workspace, clinical-form detail and invoice detail
routes now emit their authoritative access event only after successful object
scope resolution. Clinical-document and signed-report reads keep their
existing server-side audit boundary. Every separate successful resource
request is recorded; client-generated interaction identifiers are neither a
trust signal nor a deduplication key.

### Patient–Clinic document provenance

A single document-provenance validator now requires:

- the selected patient to have an active association with the resolved clinic;
- an appointment, when supplied, to match both patient and clinic.

The validator is used by manual create, patient-scoped create, upload, journey
ingestion, signed-report generation, update provenance validation and the
classification transition. Failure returns a generic not-found result and
does not create an association, document or success audit.

## Regression evidence

- client-generated unique interaction IDs create zero authoritative events;
- standalone and uploaded documents fail without an active association;
- inactive and foreign associations do not authorize a write;
- classification fails without active Patient–Clinic provenance;
- classification records a separate medical reviewer and timestamp;
- legacy clinical intent alone is not classification-review provenance;
- existing clinical document, ingestion and signed-report workflows remain
  covered by their owning suites.

## Validation recorded during implementation

- targeted sixth-rescan regressions: `7 passed`
- post-review backend fast gate: `149 passed`
- audit, prior security and document-ingestion package: `69 passed`
- clinical-document and institution-access package: `77 passed`
- signed-report package: `8 passed`
- PostgreSQL empty database upgrade to `0069`: passed
- PostgreSQL `0069 → 0068 → 0069`: passed
- populated PostgreSQL fixture: trusted reviewed record preserved; unreviewed
  legacy default demoted to `unclassified`
- backend fast suite: `149 passed`
- backend full isolated shard A: `560 passed, 1 skipped`
- backend full isolated shard B: `279 passed`
- PostgreSQL integration: `22 passed`
- production fail-closed configuration tests: `38 passed`
- frontend contract tests: `4 passed`
- frontend Vitest: `57 passed`
- frontend typecheck, smoke and production build: passed
- route-mocked Playwright: `1 passed`
- isolated PostgreSQL DB-backed Playwright: `15 passed`
- OpenAPI generation and drift check: passed
- development and synthetic production-example Compose config: passed

The three pre-existing `npm audit high` dependency findings are a separate
dependency-security follow-up and are not modified by this remediation.
GitHub CI for remediation SHA `5ef987a` passed all six current checks. A
post-review audit-ownership correction requires a new CI run before merge.
The post-merge full security rescan remains pending.

## Boundaries

PR #3 remains Draft. `main`, PR #4 and PR #7 are unchanged. Production, real
patient data and human usability are not authorized. Clinical Document Engine
work has not started.
