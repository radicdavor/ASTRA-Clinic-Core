# Program 1 Phase I6 - Backup Restore Data Integrity Governance

## Data Classes

- clinical_readiness_snapshots
- clinical readiness acknowledgment records
- clinical_findings
- clinical_open_questions
- audit records
- Alembic migration chain

## Integrity Rules

- source-linked records must retain provenance and limitations
- immutable snapshot payloads must remain historical copies
- restored data must preserve patient scope, timestamps, actor metadata and source references
- unlinked clinical truth remains no-go

## Restore Validation Checklist

- run Alembic upgrade on an empty database
- restore a backup into an isolated environment
- verify snapshot history
- verify acknowledgment history
- verify findings/open questions source links
- verify timeline read aggregation after restore
- verify audit records are present and scoped
- verify no production seed/reset scripts were used

## Decision

Production restore drills are required before production or real-data approval.

