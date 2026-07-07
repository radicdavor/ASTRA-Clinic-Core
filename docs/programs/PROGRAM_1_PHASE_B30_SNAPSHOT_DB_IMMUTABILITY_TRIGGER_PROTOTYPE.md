# Program 1 Phase B30 - Snapshot DB Immutability Trigger Prototype

Status: implementation plan for the next snapshot hardening step

## Purpose

B30 should implement the database-level immutability protection designed in B29.

The goal is to move snapshot immutability from application discipline plus regression tests toward a database-enforced invariant.

## Starting Point

B29 documented that Clinical Readiness Snapshot remains:

- demo/pilot only
- demo-data only
- not approved for production
- not approved for real patient data
- not approved for clinical enforcement

B30 may improve technical safety, but it must not change those status decisions.

## Intended Implementation

B30 should add an Alembic migration that introduces PostgreSQL protection for `clinical_readiness_snapshots`.

The implementation should protect the copied snapshot content and original capture metadata after insert.

Expected protected fields include:

- copied preview payload
- schema version
- appointment linkage
- patient linkage
- original capture timestamp
- original capture actor
- original capture reason
- copied template metadata where applicable

## Narrow Additive Exception

Supersession metadata may remain the only controlled post-insert transition.

The old snapshot may be linked to the newer replacement snapshot, but the old copied payload must remain unchanged.

B30 must preserve the rule:

`supersession is additive; historical content is not rewritten.`

## Expected Backend Regression Coverage

B30 should add tests proving:

- captured payload remains stable after supersession
- original capture reason remains stable after supersession
- appointment and patient linkage remain stable after creation
- first-time supersession metadata transition is allowed
- supersession metadata cannot be reassigned after it is set
- protected content mutation is rejected
- snapshot removal is rejected or otherwise blocked by the selected invariant
- rollback behavior remains safe

## Migration Requirements

The Alembic migration should include:

- upgrade path
- downgrade path
- clear trigger/function names
- isolated SQL function for the invariant
- comments or naming that make the clinical-safety intent obvious

## Out Of Scope

B30 must not add:

- new snapshot endpoints
- new frontend controls
- new permission labels unless required by tests
- clinical approval
- readiness clearance
- override workflow
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production approval
- real patient data approval

## Verification Gate

Recommended checks after B30 implementation:

```bash
git diff --check
python -m py_compile app/main.py app/models/domain.py app/api/routes/appointments.py app/services/clinical_readiness_snapshots.py
docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py
docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend
npm run typecheck
npm run build
npm run smoke
```

Frontend checks should pass unchanged unless B30 unexpectedly touches frontend code.

## Completion Criteria

B30 is complete only when:

- database-level invariant exists
- migration upgrade works
- migration downgrade works
- direct protected-field mutation is blocked in tests
- direct row-removal scenario is handled in tests
- existing capture, history, detail, idempotency, and supersession tests still pass
- no forbidden workflow semantics are introduced

## Recommended Next Step After B30

If B30 is implemented successfully, the next safest task is:

`Program 1 Phase B31 - Snapshot Audit Review and Retention Runbook`

Do not move to clinical enforcement after B30 alone.
