# Program 1 Phase B24 - Regression Notes

Status: snapshot supersession endpoint prototype

## Implemented

B24 izlaže B23 interni supersession service kroz uski backend endpoint.

Implementirano:

- `ClinicalReadinessSnapshotSupersedeRequest`
- `ClinicalReadinessSnapshotSupersedeResponse`
- endpoint `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}/supersede`
- permission `clinical_readiness.snapshots.supersede`
- seed mapping: admin i physician imaju permission; nurse/reception/API key nemaju runtime supersession
- endpoint regression coverage za auth, permission, API key denial, reason, scope, already-superseded conflict, audit i workflow side-effect granice

## Not implemented

B24 nije implementirao:

- frontend supersession UI
- supersession button
- edit/delete
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production governance
- real AI/OCR
- real patient data

## Behavioral Decision

Supersession endpoint je permission-gated i human-user only.

API key supersession ostaje odbijen by default, čak i ako API key ima `clinical_readiness.snapshots.supersede` scope.

Endpoint vraća novi snapshot i metadata o starom snapshotu, ali ne mijenja appointment status i ne stvara workflow objekte.

## Tests Run

Tijekom B24 pass-a pokrenuto je:

- `python -m py_compile app/main.py app/models/domain.py app/api/routes/appointments.py app/services/clinical_readiness_snapshots.py`
- `docker compose build backend`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py`

Završni puni testovi navedeni su u finalnom izvještaju cijelog B24-B28 passa.

## Remaining Risks

- frontend supersession modal još ne postoji
- permission UX ostaje osnovan
- DB-level immutability triggeri nisu implementirani
- production governance ostaje nepotpun

## Recommended Next Task

`Program 1 Phase B25 - Snapshot Supersession UI Reason Modal`
