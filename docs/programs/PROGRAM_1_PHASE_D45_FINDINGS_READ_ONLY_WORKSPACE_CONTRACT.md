# Program 1 Phase D45 - Findings Read-Only Workspace Contract

Status: documentation-only contract

## Purpose

Define the future read-only findings workspace surface without implementing UI while D33-D43 backend verification is blocked.

## Placement

The future workspace surface may appear in patient context, near existing clinical summary and evidence timeline surfaces.

Appointment context remains a future consideration and must not imply appointment readiness, clearance or workflow enforcement.

## Data Source

Future UI may use only the GET-only findings read API after backend verification passes:

- `GET /api/patients/{patient_id}/clinical-findings`
- `GET /api/patients/{patient_id}/clinical-findings/{finding_id}`

No frontend write client is allowed.

## Safe Labels

Preferred labels:

- `Source-linked findings`
- `Nalazi povezani s izvorom`
- `Za ljudski pregled`
- `Nije dijagnoza`
- `Ne mijenja status termina`

Forbidden labels:

- approved
- cleared
- resolved
- diagnosis confirmed
- treatment started
- task completed
- outcome documented
- patient notified

## States

The future UI must define:

- loading state
- empty state
- read error state
- permission denied state
- source missing/stale state

Empty state means no persisted findings are visible. It must not mean there is no clinical risk.

## No-Action Boundary

The workspace must not include:

- acknowledge/review button
- approve button
- clear button
- override button
- resolve button
- create task button
- send patient message button

## Safety Boundary

The read-only workspace must present findings as source-linked context for human review. It must not present findings as diagnosis, treatment plan, approval, clearance, override, Task, Outcome Evidence or patient instruction.

## Implementation Gate

No frontend implementation may begin until D33-D43 targeted and full backend tests pass.

