# Program 1 Phase D34 - Findings Read Response Schema Contract

Status: schema contract

## List Item Response

Findings read list items include:

- finding id and key
- patient id
- source type, label, reference and optional source document id
- label and category
- lifecycle status
- requires review flag
- optional review metadata
- limitations
- schema version
- created and updated timestamps
- safe no-decision disclaimer

## Detail Response

Detail response uses the same safe shape plus a read-only warning.

## Forbidden Fields

Responses must not include:

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

## Runtime Boundary

The schemas are response-only. They do not add endpoint, service, UI or write behavior.

