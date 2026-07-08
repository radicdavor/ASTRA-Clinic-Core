# Program 1 Phase D125 Regression Notes

Status: GET-only read API prototype added

## Completed

- Added `GET /api/patients/{patient_id}/clinical-open-questions`.
- Added `GET /api/patients/{patient_id}/clinical-open-questions/{question_id}`.
- Added optional `finding_id` list filter with patient-scope validation.
- Required authenticated user with `clinical_open_questions.read`.
- Kept API keys denied through user-only read boundary.

## Runtime Behavior

The new behavior is read-only and source-linked. It does not write audit events by default and does not mutate patients, findings, open questions, appointments or source documents.

## Safety Boundary

No POST, PATCH, PUT, DELETE, review, approve, clear, resolve, task, outcome, message, diagnosis or treatment route was added.
