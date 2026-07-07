# Program 1 Phase B31 - Snapshot Audit Review and Retention Runbook

Status: demo/pilot audit review and retention runbook

## Purpose

This runbook defines how Clinical Readiness Snapshot audit events should be reviewed, retained, exported and interpreted in demo/pilot context.

It is not production approval, real-data approval, compliance approval, certified EMR documentation or medical-device documentation.

## Snapshot Audit Events

Current snapshot audit events:

- `clinical_readiness_snapshot_captured`
- `clinical_readiness_snapshot_superseded`

Capture audit event records that a user saved a server-side Clinical Readiness Preview as a snapshot.

Supersession audit event records that a user created a newer preview snapshot and marked an older snapshot as superseded.

Neither event means:

- clinical approval
- readiness clearance
- procedure permission
- workflow override
- Outcome Evidence
- Task completion
- appointment status change

## Minimal Capture Audit Payload

Capture payload should remain stable enough for demo/pilot review:

- snapshot id
- appointment id
- patient id
- service id
- actor/user id
- capture reason
- schema version
- preview generated timestamp
- preview status
- template key/label/version
- template binding status
- item count
- blocking item count
- limitation count
- source warning count
- preview snapshot marker
- disclaimer

## Minimal Supersession Audit Payload

Supersession payload should include:

- old snapshot id
- new snapshot id
- appointment id
- patient id
- service id
- actor/user id
- supersede reason
- old/new template key
- old/new template version
- old/new preview status
- old/new created timestamp
- preview snapshot marker

## Audit Is Not Outcome Evidence

Audit proves that a system event happened.

Audit does not prove that:

- a clinical outcome occurred
- a procedure was safe to perform
- a physician approved readiness
- a patient was ready
- a task was completed

Outcome Evidence remains out of scope.

## Retention Assumptions

For demo/pilot:

- audit events are retained in the application database
- audit events are not automatically purged
- snapshot rows are not deleted
- retention is not production policy
- no legal retention period is claimed

Before production:

- retention policy must be approved by maintainers
- backup policy must include audit tables
- restore validation must prove audit/snapshot consistency
- access-control review must define who can inspect audit rows

## Export Assumptions

Demo/pilot export may use existing read-only audit access where available.

Export must not:

- create clinical decisions
- message patients
- expose real patient data
- imply production readiness
- imply regulatory compliance

Allowed export fields should be limited to event metadata, actor metadata and snapshot ids needed for review.

## Restore Assumptions

Restore must preserve:

- snapshot rows
- audit rows
- old/new snapshot relationship
- idempotency metadata
- DB immutability triggers
- migration order

If restore loses audit events, snapshot history becomes incomplete and must be treated as demo/pilot no-go until investigated.

## Manual Review Process

Demo/pilot manual review:

1. Open Appointment Workspace.
2. Review snapshot history and detail.
3. Review Audit Log filtered by `ClinicalReadinessSnapshot` or snapshot audit action.
4. Compare capture/supersession reasons with stored snapshot detail.
5. Confirm no audit wording implies clinical approval or clearance.
6. Record findings in pilot notes, not as patient-facing clinical output.

## Not Production-Ready

Not production-ready:

- retention policy
- export policy
- legal wording
- real-data access control
- backup/restore drill
- audit review workflow
- incident response

## Recommended Next Task

`Program 1 Phase B32 - Snapshot Audit Payload Stabilization`
