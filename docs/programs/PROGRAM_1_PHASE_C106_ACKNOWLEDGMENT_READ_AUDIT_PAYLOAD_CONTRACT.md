# Program 1 Phase C106 - Acknowledgment Read Audit Payload Contract

Status: payload contract

## Purpose

C106 defines the minimum future payload for acknowledgment read audit events.

No runtime audit event is implemented in this phase.

## Allowed Payload Fields

Future read audit payload may include:

- event name
- actor id
- actor role
- actor type
- appointment id
- patient id if safely resolved
- acknowledgment id if applicable
- access type: `list`, `detail`, `denied`, `failed`
- request id
- timestamp
- result status
- safe error category

## Denied/Failed Safe Categories

Safe categories may include:

- unauthenticated
- missing_permission
- api_key_denied
- non_human_actor_denied
- appointment_not_found
- acknowledgment_not_found
- appointment_scope_mismatch
- unexpected_error

## Forbidden Payload Fields

Payload must not include:

- full clinical reason text unless explicitly approved later
- approval_status
- clearance_status
- override_status
- outcome_evidence_id
- task_id
- appointment_status mutation
- patient_message_id
- clinical conclusion
- patient-ready status

## Minimization Rule

Read audit should capture access/security context, not clinical content.

Denied-read payload should be especially careful not to leak whether a record exists in another appointment context.

## Boundary

Read audit payload is not Outcome Evidence, Task evidence, clinical approval or readiness clearance.

