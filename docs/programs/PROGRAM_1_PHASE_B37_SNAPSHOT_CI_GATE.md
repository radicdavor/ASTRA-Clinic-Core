# Program 1 Phase B37 - Snapshot CI Gate

Status: CI gate documentation and explicit targeted test step

## Purpose

This document defines the required Clinical Readiness Snapshot regression gate before merge or release.

The gate protects snapshot preview/capture/history/detail/supersession behavior from accidental workflow expansion.

## Required Checks

Snapshot gate checks:

- `git diff --check`
- backend Python compile
- targeted snapshot backend tests
- full backend suite
- frontend typecheck
- frontend build
- frontend smoke
- Alembic migration upgrade in CI

## CI Coverage

CI now runs:

- database migrations
- targeted snapshot regression gate:
  - `python -m pytest tests/test_clinical_readiness_snapshots.py`
- full backend suite:
  - `python -m pytest`
- frontend typecheck
- frontend smoke
- frontend build

## Snapshot Behaviors Protected

Protected:

- preview GET is read-only
- capture requires reason and permission
- capture writes stable audit payload
- history/detail remain read-only
- idempotency guard works
- supersession is additive
- DB immutability blocks protected mutation/deletion
- no workflow side effects are created

## Forbidden Behaviors

CI/smoke must continue to guard against:

- clinical approval
- readiness clearance
- override workflow
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- forbidden frontend wording

## Migration Gate

CI runs Alembic upgrade before backend tests.

Snapshot DB immutability trigger must remain compatible with migration upgrade.

## Production Status

This CI gate improves confidence but does not grant production approval or real patient data approval.

## Recommended Next Task

`Program 1 Phase B38 - Snapshot Legal/Compliance Disclaimer Review`
