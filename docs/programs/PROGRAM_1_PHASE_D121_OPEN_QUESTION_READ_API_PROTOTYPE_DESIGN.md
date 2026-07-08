# Program 1 Phase D121 - Open Question Read API Prototype Design

Status: designed before implementation

## Implemented Route Scope

The D121 prototype may implement only patient-scoped GET routes:

- `GET /api/patients/{patient_id}/clinical-open-questions`
- `GET /api/patients/{patient_id}/clinical-open-questions/{question_id}`

An optional `finding_id` query filter may narrow the list to questions linked to a finding owned by the same patient.

## GET-Only Boundary

The prototype must not add POST, PATCH, PUT, DELETE, review, approve, clear, resolve, task, outcome or patient-message routes.

## Scope and Permission Requirements

- Authentication is required.
- A read-only permission may be added if required by the existing permission model.
- API keys remain denied for this sensitive read surface.
- Detail reads must hide out-of-scope questions.

## Response Shape

Responses must use source-linked read schemas and include:

- question id/key
- patient id
- linked finding id if present
- source type, source label and source reference summary
- status
- requires clinician review
- limitations
- created and updated timestamps
- no-decision disclaimer

## Safety Boundary

The read API does not create, review, approve, clear, resolve, diagnose, treat, notify, schedule or close anything. It does not create Task, Outcome Evidence, patient message, appointment status mutation or workflow enforcement.

## Production and Real-Data Status

D121 remains a prototype for demo/pilot development only. It does not approve production or real patient data use.
