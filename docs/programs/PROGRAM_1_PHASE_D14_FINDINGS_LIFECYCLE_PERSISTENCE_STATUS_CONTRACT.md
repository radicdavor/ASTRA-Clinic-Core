# Program 1 Phase D14 - Findings Lifecycle Persistence Status Contract

Status: lifecycle persistence contract

## Allowed Persisted Statuses

Use the D2 status set:

- `received`
- `linked_to_patient`
- `awaiting_review`
- `review_in_progress`
- `reviewed`
- `needs_clinician_decision`
- `decision_documented`
- `follow_up_recommended`
- `external_referral_recommended`
- `closed_for_now`

## Forbidden Semantics

Persisted status must not trigger:

- workflow automation
- patient notification
- Task creation
- Outcome Evidence creation
- appointment status mutation
- diagnosis confirmation
- treatment start
- readiness clearance

## Transition Rules

Future implementation must validate transitions explicitly.

`reviewed` is not diagnosis.

`decision_documented` means a separate decision exists or is referenced; it is not the finding row itself.

`closed_for_now` is temporary lifecycle state, not permanent closure, cure or Outcome Evidence.

## Interpretation

Only authorized clinical users may interpret clinical meaning.

Nurse/reception/system roles may see operational context only if later policy permits.

## Runtime Boundary

D14 does not implement status transitions.

