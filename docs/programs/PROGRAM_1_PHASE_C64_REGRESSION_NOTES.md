# Program 1 Phase C64 - Regression Notes

Status: internal service prototype

## Implemented

- added internal-only acknowledgment write service prototype
- service requires non-empty reason
- service requires human actor user id and actor role
- service rejects API key, system, system job and AI-agent style actor roles
- service verifies appointment/patient scope
- service verifies current advisory signal key in the read-only preview context
- service verifies optional snapshot appointment/patient scope
- service inserts passive `ClinicalReadinessReviewAcknowledgment`
- service writes audit event `clinical_readiness_acknowledged`
- insert and audit write commit once in the same transaction

## Behavioral Boundary

The service is not exposed through an API route.

No frontend action, permission seed or runtime acknowledgment endpoint was added.

## Not Implemented

- acknowledgment endpoint
- frontend write client
- UI action button
- permission seed
- idempotency storage
- approval
- readiness clearance
- override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging
- real patient data
- production readiness

## Audit Naming Decision

The audit action is `clinical_readiness_acknowledged` to stay within the existing `audit_logs.action` length.

The event means only that a human review acknowledgment row was written. It is not Outcome Evidence and not clinical approval.

## Remaining Risks

- no route-level permission exists because no route exists
- no user-facing reason UX exists
- idempotency remains deferred
- advisory signal freshness is limited to current preview key validation

