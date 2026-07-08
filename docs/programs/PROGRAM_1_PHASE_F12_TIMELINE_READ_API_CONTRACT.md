# Program 1 Phase F12 - Timeline Read API Contract

Status: documented, no endpoint

## Future Route Proposal

- `GET /api/patients/{patient_id}/clinical-evidence-timeline`

## Boundary

The future route would be patient-scoped, authenticated and permission gated. Optional filters may include source type, event type, date range and requires-review flag.

## Response Shape

Response should include timeline event previews with event key/type, label, source reference, timestamps, limitations, requires-review flag and no-decision disclaimer.

## No-Go

No endpoint is implemented in this phase. No write behavior, Task, Outcome Evidence, patient message, diagnosis, treatment, approval, clearance or override is allowed.
