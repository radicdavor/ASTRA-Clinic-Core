# Program 1 Phase C27 - Acknowledgment Persistence Design

Status: design-only persistence model

## Purpose

This document defines a future persistence model for Human Review Acknowledgment.

C27 does not implement a DB model, migration, endpoint, service or UI action.

## Proposed Entity

Entity name:

`ClinicalReadinessReviewAcknowledgment`

Proposed table name:

`clinical_readiness_review_acknowledgments`

## Relationships

Future acknowledgment should reference:

- `appointment_id`
- `patient_id`
- `advisory_signal_key`
- `snapshot_id` when the reviewed signal came from a saved snapshot
- `actor_user_id`
- `actor_role`

## Required Fields

- `id`
- `appointment_id`
- `patient_id`
- `advisory_signal_key`
- `snapshot_id`
- `reason`
- `actor_user_id`
- `actor_role`
- `created_at`
- `limitations_json`
- `not_decision_disclaimer`

## Reason Required

Reason must be required.

Whitespace-only reason must be rejected.

## Immutable Fields

Future persistence should treat these as immutable after insert:

- appointment reference
- patient reference
- advisory signal reference
- snapshot reference
- reason
- actor metadata
- created timestamp
- disclaimer

## Explicitly Forbidden Links

The persistence model must not include:

- appointment status mutation
- Task link
- Outcome Evidence link
- patient message link
- approval status
- clearance status
- override status

## Retention Assumptions

Acknowledgment records should be retained as review history for the demo/pilot audit trail.

Retention does not imply production approval or compliance readiness.

## Audit Relationship

If persistence is implemented later, creation must write an audit event.

The audit event records review context only.

It must not imply approval, clearance, override, task completion or outcome.

## Conclusion

Persistence design is allowed.

Runtime endpoint remains no-go.

UI action remains no-go.

Migration remains deferred unless a future phase explicitly approves a draft/no-runtime migration.

