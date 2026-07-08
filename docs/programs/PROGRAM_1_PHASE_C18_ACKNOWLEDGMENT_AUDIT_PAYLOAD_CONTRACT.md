# Program 1 Phase C18 - Acknowledgment Audit Payload Contract

Status: documentation-only audit contract

## Purpose

This document defines the future audit payload if Human Review Acknowledgment is ever implemented.

C18 does not implement a runtime audit event.

## Proposed Event Name

`clinical_readiness_advisory_review_acknowledged`

## Required Payload Fields

- `actor_user_id`
- `actor_role`
- `appointment_id`
- `patient_id`
- `advisory_signal_key`
- `advisory_signal_label`
- `snapshot_id`
- `reason`
- `acknowledged_at`
- `limitations`
- `is_decision: false`
- `is_clearance: false`
- `is_override: false`

## Explicitly Forbidden Payload Fields

- `approval_status`
- `clearance_status`
- `override_status`
- `outcome_evidence_id`
- `task_id`
- `appointment_status_after`
- `patient_message_id`
- `procedure_approved`
- `patient_ready`

## Audit Meaning

The audit event would mean:

- a human reviewed a signal
- a reason was recorded
- context was captured

The audit event would not mean:

- procedure approved
- patient cleared
- readiness risk resolved
- task completed
- outcome documented
- patient notified

## Snapshot Relationship

If a snapshot is referenced, the snapshot payload must remain unchanged.

Historical clinical/capture content must not be rewritten.

## Runtime Scope

No endpoint, DB model, persistence or audit writer is implemented in C18.

