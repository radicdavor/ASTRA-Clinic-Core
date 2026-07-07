# Program 1 Phase B23 - Regression Notes

Status: internal snapshot supersession service prototype

## Implemented

B23 uvodi samo backend service-layer supersession za Clinical Readiness Snapshot.

Implementirano:

- refactor capture internala u helper koji moze raditi bez vlastitog commita
- interni service `supersede_clinical_readiness_snapshot(...)`
- stvaranje novog server-side preview snapshota u istoj transakciji
- oznacavanje starog snapshota kao zamijenjenog
- audit event `clinical_readiness_snapshot_superseded`
- regresijska pokrivenost za validacije, appointment scope, rollback, audit payload i workflow side-effect granice

## Not implemented

B23 nije implementirao:

- supersession endpoint
- frontend supersession UI
- supersession button
- snapshot edit
- snapshot delete
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

Supersession je aditivna povijesna veza:

- stari snapshot ostaje spremljen
- stari snapshot payload ostaje nepromijenjen
- novi snapshot se kreira iz trenutnog server-side previewa
- stari snapshot pokazuje na novi snapshot kroz supersession metadata
- audit event zapisuje zamjenu
- supersession ne znaci da je stari snapshot bio pogresan
- supersession ne znaci da je pacijent spreman
- supersession ne odobrava postupak

Novi snapshot u B23 dobiva `snapshot_reason` u obliku:

`Supersession: <razlog>`

Stari snapshot cuva izvorni `snapshot_reason`, disclaimer, template metadata, preview status i JSON copied payload.

## Safety Properties

B23 cuva:

- capture endpoint behavior ostaje nepromijenjen
- idempotency behavior iz B20 ostaje nepromijenjen za normalni capture
- preview GET ostaje non-persistent
- history/detail endpointi ostaju read-only
- nema javnog supersession endpointa
- nema frontend UI-ja
- nema approval/clearance/override semantike
- nema Outcome Evidence ili Task objekta
- nema appointment status promjene

## Tests Run

Tijekom B23 pass-a pokrenuto je:

- `python -m py_compile app/main.py app/models/domain.py app/api/routes/appointments.py app/services/clinical_readiness_snapshots.py`
- `docker compose build backend`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py`

Zavrsni puni testovi navedeni su u finalnom izvjestaju ovog taska.

## Remaining Risks

- nema route-level permissiona jer endpoint ne postoji
- nema frontend UI-ja
- nema user-facing reason modala za supersession
- DB-level immutability triggeri nisu implementirani
- idempotency vrijedi za normalni capture; supersession idempotency nije posebno dizajniran
- production governance ostaje nepotpun

## Recommended Next Task

`Program 1 Phase B24 - Snapshot Supersession Endpoint Prototype`

B24 smije izloziti supersession kroz endpoint tek nakon sto B23 service testovi prolaze.
