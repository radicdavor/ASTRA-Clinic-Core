# Program 1 Phase B34 - Snapshot Backup Restore Consistency Runbook

Status: demo/pilot backup and restore consistency runbook

## Purpose

This runbook defines how backup and restore must preserve Clinical Readiness Snapshot consistency.

It is not production approval and does not authorize real patient data.

## Objects That Must Be Preserved

Restore must preserve:

- `clinical_readiness_snapshots` rows
- `audit_logs` rows for snapshot capture and supersession
- appointment relationship
- patient relationship
- service relationship
- superseded-by snapshot relationship
- idempotency key and fingerprint
- immutable DB trigger/function

## Snapshot Row

Snapshot row content must remain unchanged after restore:

- copied preview payload JSON
- preview summary/status
- template metadata
- capture reason
- disclaimer
- actor user id
- created timestamp

## Audit Event Row

Audit rows must remain readable and linked by:

- action
- entity type
- entity id
- snapshot ids inside payload
- appointment id
- patient id
- service id

## Supersession Relationship

For superseded snapshots:

- old snapshot remains stored
- old snapshot points to replacement snapshot
- replacement snapshot exists
- old snapshot payload is unchanged
- supersession reason is preserved

## Idempotency Metadata

Restore must preserve:

- idempotency key
- idempotency fingerprint

If idempotency metadata is lost, duplicate-capture protection becomes incomplete.

## DB Immutability Trigger After Restore

Restore validation must confirm:

- update trigger exists
- delete trigger exists
- protected-field mutation fails
- row deletion fails
- first-time supersession transition remains possible for non-superseded rows

## Alembic Migration Order

Expected migration order:

1. snapshot table creation
2. snapshot idempotency metadata
3. snapshot DB immutability trigger

Restore must not apply immutability trigger before required columns exist.

## Restore Validation Checklist

After restore:

1. Run Alembic status/check.
2. Query snapshot count.
3. Query snapshot audit count.
4. Verify every superseded snapshot points to an existing replacement snapshot.
5. Verify every snapshot has appointment, patient and service ids.
6. Verify capture audit payload references existing snapshot.
7. Verify supersession audit payload references existing old/new snapshots.
8. Attempt protected-field mutation in a non-production validation database.
9. Attempt snapshot deletion in a non-production validation database.
10. Run snapshot regression tests.

## Demo/Pilot Limitations

This runbook is for demo/pilot hardening.

It does not define:

- production backup SLA
- legal retention period
- incident response
- real patient data approval
- certified EMR retention policy

## Recommended Next Task

`Program 1 Phase B35 - Snapshot Restore Validation Regression`
