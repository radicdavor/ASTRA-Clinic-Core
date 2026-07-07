# Program 1 Phase B29 - Snapshot DB Immutability Trigger Design

Status: design-only database hardening contract

## Purpose

This document defines the database-level immutability rule that should exist before Clinical Readiness Snapshot is considered for production-risk review.

Application-level discipline is useful, but production-risk hardening requires a database invariant too.

## Protected Snapshot Data

The protected data is the copied snapshot record captured at a specific time.

Protected fields should include:

- copied preview payload JSON
- snapshot schema version
- appointment linkage
- patient linkage
- template metadata copied into the snapshot
- original capture timestamp
- original capture actor
- original capture reason

## Narrow Supersession Exception

Supersession remains additive.

The old snapshot may receive metadata that links it to a newer snapshot, but its copied payload must remain unchanged.

The narrow mutable fields are expected to be limited to:

- superseded marker
- superseded timestamp
- replacement snapshot id
- supersession actor
- supersession reason

## Database Invariants

A future PostgreSQL trigger should enforce:

- copied payload is stable after insert
- original capture metadata is stable after insert
- appointment and patient scope are stable after insert
- a snapshot row is append-only from the perspective of clinical content
- supersession metadata can be written only as a controlled additive transition
- supersession metadata cannot be reassigned after it is set

## Recommended Trigger Shape

Recommended hardening path:

1. Add a database function that compares old and new row values.
2. Add a BEFORE UPDATE trigger on `clinical_readiness_snapshots`.
3. Add a row-removal guard for `clinical_readiness_snapshots`.
4. Permit only the narrow first-time supersession transition.
5. Reject changes to protected clinical-content fields.

## Regression Expectations

When implemented, backend tests should prove:

- copied payload remains unchanged across supersession
- original reason remains unchanged across supersession
- appointment and patient scope remain unchanged
- replacement metadata can be set once
- replacement metadata cannot be reassigned
- attempted protected-field mutation fails
- rollback behavior remains safe

## Migration Caution

Before implementation:

- inspect existing demo rows
- confirm Alembic upgrade and downgrade strategy
- confirm local demo seed compatibility
- confirm test database reset behavior
- confirm that repair workflows are maintenance-only and not normal runtime behavior

## Gate Implication

Until this invariant is implemented and tested, snapshot persistence remains:

- allowed for closed demo/pilot with demo data only
- no-go for real patient data
- no-go for production
- no-go for clinical enforcement

## Explicit Non-Goals

This design does not authorize:

- clinical approval
- readiness clearance
- override workflow
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production claims
