# Program 1 Phase D111 - Open Question Read Response Schema Contract

Status: passive schema contract

## List Item Response

List item responses include:

- question id/key
- patient id
- linked finding id when available
- source type, label and reference summary
- label
- status
- `requires_clinician_review`
- review timestamp and reviewer id when safe
- limitations
- created/updated timestamps
- no-decision disclaimer

## Detail Response

Detail responses may include full source reference, linked finding key and optional review note. Detail response still must not imply diagnosis, recommendation, decision, resolution, task, outcome evidence or patient communication.

## Forbidden Fields

- `diagnosis_confirmed`
- `treatment_plan`
- `patient_notified`
- `task_id`
- `outcome_evidence_id`
- `approval_status`
- `clearance_status`
- `resolved_by_ai`
- `patient_message_id`
- `appointment_status`
- `auto_closed_at`

## Runtime Boundary

The response schemas are passive. No endpoint, service, frontend client or UI is added in this phase.
