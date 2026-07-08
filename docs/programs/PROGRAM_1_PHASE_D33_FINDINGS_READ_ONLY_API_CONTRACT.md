# Program 1 Phase D33 - Findings Read-Only API Contract

Status: contract

## Purpose

Define a read-only API boundary for persisted clinical findings.

The read API exposes source-linked finding context for demo/pilot review. It does not create clinical decisions, diagnosis, treatment plans, Tasks, Outcome Evidence, patient messages or workflow enforcement.

## Proposed Routes

- `GET /api/patients/{patient_id}/clinical-findings`
- `GET /api/patients/{patient_id}/clinical-findings/{finding_id}`

Future appointment context may be considered separately:

- `GET /api/appointments/{appointment_id}/clinical-findings`

## Scope Boundary

The initial boundary is patient-scoped.

Detail reads must require both:

- the requested patient exists
- the requested finding belongs to that patient

Out-of-scope detail reads must return not found and must not reveal another patient's finding details.

## Auth and Permission

Read access requires authentication and a dedicated read permission proposal:

`clinical_findings.read`

This permission does not imply write, review, diagnosis, treatment, approval, clearance or override authority.

API key and AI agent access remain restricted unless a later phase explicitly approves a read-only integration.

## Response Shape

List items should include:

- finding id and key
- patient id
- source reference summary
- label
- category
- lifecycle status
- requires review flag
- review metadata if present
- limitations
- created and updated timestamps
- safe no-decision disclaimer

Detail responses may include full source reference fields and review metadata.

## Sorting and Filtering

Default sorting is newest first by `created_at`, then id.

Future filters may include:

- lifecycle status
- category
- requires review
- source type

## Empty State

An empty list means no persisted findings are visible for that patient. It does not mean the patient has no clinical risk or that review is complete.

## No-Go Runtime Semantics

The read API must not:

- mutate findings
- create or update Tasks
- create Outcome Evidence
- send patient messages
- change appointment status
- diagnose or treat
- approve, clear or override readiness

## Production Boundary

This contract does not approve production use or real patient data.

