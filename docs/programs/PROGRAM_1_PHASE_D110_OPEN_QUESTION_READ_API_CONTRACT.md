# Program 1 Phase D110 - Open Question Read API Contract

Status: contract only

## Proposed GET Routes

- `GET /api/patients/{patient_id}/clinical-open-questions`
- `GET /api/patients/{patient_id}/clinical-open-questions/{question_id}`
- optional future: `GET /api/patients/{patient_id}/clinical-findings/{finding_id}/open-questions`

These routes are contract proposals only. No endpoint is implemented in this phase.

## Read Boundaries

- patient-scoped list returns open questions for one patient only
- finding-scoped list must also validate patient scope
- detail read must not reveal out-of-scope question existence
- reads are source-linked, no-decision surfaces

## Auth And Permission Expectations

Future read access requires authenticated user context and a dedicated read permission. Read permission does not imply write, review, approval, clearance, resolve, tasking, messaging or diagnosis authority.

## Response Shape

Responses must include question key/id, patient id, linked finding id if any, source reference summary, label, safe status, clinician review requirement, limitations, timestamps and no-decision disclaimer.

## Sorting And Filtering

Default list sorting should be newest-first. Future filters may include status, `requires_clinician_review`, linked finding and source type. Filters must not create workflow side effects.

## Empty And Error States

An empty list means no visible source-linked questions for that scope. It does not mean no clinical risk, no open clinical work or patient readiness.

Unknown or out-of-scope resources should return safe not-found or denied behavior without clinical decision wording.

## Explicit Non-Goals

- no write behavior
- no automatic question creation
- no Task, Outcome Evidence or patient messaging
- no diagnosis, treatment, approval, clearance or override
- no production or real-data approval
