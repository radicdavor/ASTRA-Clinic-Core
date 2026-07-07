# Program 1 Phase B9 - Regression Notes

Status: documentation-only persistence design

## Implemented

Phase B9 definira buduci persistence model za Clinical Readiness Snapshot prije bilo kakve implementacije.

Implementirano:

- snapshot persistence model design
- snapshot audit model design
- snapshot lifecycle governance design
- snapshot future regression gate

Novi dokumenti:

- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_PERSISTENCE_MODEL.md`
- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_AUDIT_MODEL.md`
- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_LIFECYCLE_GOVERNANCE.md`
- `PROGRAM_1_PHASE_B9_CLINICAL_READINESS_SNAPSHOT_REGRESSION_GATE.md`

## Behavioral changes

Nema behavioral changes.

B9 ne mijenja backend, frontend, API response, bazu, migracije ili UI.

## Not implemented

B9 nije implementirao:

- DB tablicu
- Alembic migraciju
- snapshot capture endpoint
- snapshot history UI
- persistent snapshot model
- audit events
- Outcome Evidence
- enforcement
- override
- Task engine
- Workflow Engine
- real AI/OCR
- real patient data

## Remaining risks

- persistent snapshot jos ne postoji
- schema nije implementirana
- capture endpoint ne postoji
- audit implementation ne postoji
- history UI ne postoji
- production governance ne postoji
- migration rollback rizici nisu jos pregledani

## B9 decision

Clinical Readiness Snapshot persistence smije ici prema buducem modelu samo ako ostane:

- explicit capture
- immutable copied payload
- preview-only
- auditiran capture
- bez appointment status promjene
- bez taskova
- bez Outcome Evidencea
- bez clinical approval znacenja

Najvaznija odluka:

Snapshot persistence sprema ono sto je preview prikazao, ne ono sto sustav kasnije moze recomputeati.

## Recommended next task

`Program 1 Phase B10 - Snapshot Persistence Migration Review`

Razlog:

Prije Alembic migracije treba posebno pregledati table shape, naming, indexes, JSON fields, audit event naming, immutability constraints i rollback rizike.

Alternativni brzi put `Clinical Readiness Snapshot Persistence Prototype` nije preporucen bez tog migration reviewa.

## Follow-up after B10/B11 design

B10 je odvojen kao migration review prije Alembic migracije.

B11 je odvojen kao capture endpoint design prije backend rute.

Oba koraka ostaju documentation-only i ne mijenjaju B9 odluku:

Snapshot persistence smije spremiti samo immutable kopiju preview prikaza, uz eksplicitni capture i buduci audit. Snapshot ne smije postati clinical approval, Outcome Evidence, Task, override ili appointment status.
