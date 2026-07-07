# Program 1 Phase B30 - Regression Notes

Status: Snapshot DB Immutability Trigger Prototype

## Implemented

B30 dodaje DB-level invariant za `clinical_readiness_snapshots`.

Implementirano:

- nova Alembic migracija:
  - `0016_snapshot_db_immutability`
- PostgreSQL `BEFORE UPDATE` trigger za snapshot immutability
- PostgreSQL `BEFORE DELETE` trigger za zabranu brisanja snapshot redova
- SQLite trigger DDL kroz SQLAlchemy model event za postojece test fixture okruzenje
- narrow first-time additive supersession metadata transition ostaje dopusten
- protected clinical/capture content ostaje nepromjenjiv nakon inserta

## Protected Fields

DB invariant stiti:

- appointment linkage
- patient linkage
- service linkage
- original created_at
- original capture actor
- schema version
- preview timestamp/status/summary
- copied template metadata
- copied preview payload JSON
- disclaimer
- original capture reason
- idempotency key/fingerprint

## Allowed Narrow Transition

Dopusten je samo prvi prijelaz iz:

- `superseded_by_snapshot_id = null`
- `superseded_at = null`
- `superseded_reason = null`

u stanje gdje su sva tri supersession metadata polja postavljena.

Nakon toga se supersession metadata ne moze ponovno dodijeliti drugom replacement snapshotu.

## Tests Added Or Extended

Prosireni su backend snapshot testovi:

- direct copied payload mutation se odbija
- original capture reason mutation se odbija
- appointment linkage reassignment se odbija
- patient linkage reassignment se odbija
- first-time supersession metadata transition radi
- supersession metadata reassignment se odbija
- snapshot row deletion se odbija
- post-rollback stanje ostaje sigurno
- postojece capture/history/detail/idempotency/supersession regresije i dalje prolaze
- workflow side effects se ne stvaraju

## Safety Boundaries Preserved

B30 ne mijenja:

- API contract
- frontend UI
- appointment status
- capture semantics
- supersession semantics
- permission model

B30 cuva:

- supersession is additive
- old snapshot payload remains unchanged
- old snapshot clinical/capture content is not rewritten
- snapshot state does not enforce clinical workflow

## Not Implemented

B30 nije implementirao:

- clinical approval
- readiness clearance
- override workflow
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production approval
- real patient data approval
- real AI/OCR
- autonomous clinical decision-making
- maintenance repair workflow

## Tests Run

Tijekom B30 pass-a pokrenuto je:

- `docker compose build backend`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py`

Final required checks trebaju se pokrenuti prije B30 commita:

- `git diff --check`
- `python -m py_compile app/main.py app/models/domain.py app/api/routes/appointments.py app/services/clinical_readiness_snapshots.py`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_snapshots.py`
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend`
- `npm run typecheck`
- `npm run build`
- `npm run smoke`

## Remaining Risks

- PostgreSQL trigger je prototip i treba review prije produkcijskog okruzenja
- nema maintenance-only repair workflowa za pogresno unesene demo snapshotove
- production governance ostaje nepotpun
- real patient data ostaje no-go
- clinical enforcement ostaje no-go

## Recommended Next Task

`Program 1 Phase B31 - Snapshot Audit Review and Retention Runbook`
