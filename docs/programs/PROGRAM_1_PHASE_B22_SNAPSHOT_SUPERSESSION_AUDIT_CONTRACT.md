# Program 1 Phase B22 - Snapshot Supersession Audit Contract

Status: documentation-only audit contract

## Purpose

This document defines the future audit semantics for Clinical Readiness Snapshot supersession.

It does not implement audit writes, endpoints, services, UI, schema or migration.

## Future Audit Event

Future event name:

`clinical_readiness_snapshot_superseded`

## Required Payload

Future payload:

```json
{
  "old_snapshot_id": 123,
  "new_snapshot_id": 124,
  "appointment_id": 456,
  "patient_id": 789,
  "service_id": 10,
  "actor_user_id": 5,
  "supersede_reason": "New snapshot after reviewed pathology.",
  "old_template_key": "colonoscopy",
  "old_template_version": "demo-v1",
  "new_template_key": "colonoscopy",
  "new_template_version": "demo-v1",
  "old_preview_status": "ready_with_warning",
  "new_preview_status": "not_ready",
  "old_created_at": "2026-07-07T10:30:00Z",
  "new_created_at": "2026-07-07T11:00:00Z"
}
```

Required fields:

- old snapshot id
- new snapshot id
- appointment id
- patient id
- service id
- actor user id
- supersede reason
- old template key/version
- new template key/version
- old preview status
- new preview status
- old created_at
- new created_at

## Audit Meaning

The audit event means:

`User marked an older immutable preview snapshot as superseded by a newer immutable preview snapshot.`

## Audit Must Not Imply

The event must not imply:

- approval
- clearance
- override
- task completion
- outcome
- appointment status change
- old snapshot deletion
- old snapshot payload edit
- patient messaging

## Transaction Boundary

Future implementation should update supersession metadata and write audit event in one transaction.

If audit write fails, supersession must fail.

If supersession metadata update fails, audit must not remain as a false record.
