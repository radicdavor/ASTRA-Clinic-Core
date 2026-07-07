# Program 1 Phase B8 - Regression Notes

Status: Clinical Readiness Snapshot design and non-implementation transparency

## Implemented

Phase B8 uvodi design dokumente i minimalni runtime transparency metadata sloj za buduci Clinical Readiness Snapshot.

Implementirano:

- snapshot design document
- snapshot boundaries document
- preview response exposes snapshot non-implementation metadata
- Appointment Workspace displays snapshot warning
- regression coverage for snapshot non-persistence and read-only behavior

Nova preview response metadata polja:

- `snapshot_supported`
- `snapshot_status`
- `snapshot_warning`

Trenutne demo vrijednosti:

- `snapshot_supported=false`
- `snapshot_status="not_implemented"`
- `snapshot_warning="Snapshot nije implementiran. Ovaj prikaz je live read-only preview i ne sprema se kao trajni zapis."`

## Behavioral changes

`GET /api/appointments/{appointment_id}/clinical-readiness-preview` ostaje ista read-only putanja.

Response sada eksplicitno govori da snapshot nije implementiran.

Appointment Workspace prikazuje:

- `Snapshot: nije implementiran`
- upozorenje da se live preview ne sprema kao trajni zapis

Nema capture akcije, spremanja, history prikaza ili workflow promjene.

## Not implemented

B8 nije implementirao:

- persistent snapshot model
- DB tablicu
- Alembic migraciju
- snapshot capture endpoint
- snapshot history UI
- audit event za snapshot capture
- Outcome Evidence
- enforcement
- override
- Task engine
- Workflow Engine
- real AI/OCR
- real patient data

## Safety properties

B8 cuva:

- endpoint je read-only
- preview je appointment-scoped
- preview je non-blocking
- snapshot metadata je transparency layer
- `snapshot_supported=false`
- nema snapshot persistencea
- nema appointment status promjene
- nema audit writea za obican preview read
- nema task creationa
- nema episode creationa
- nema ClinicalPlan creationa
- nema Outcome Evidence creationa
- nema production/certification claima

## Tests/checks

Ciljani B8 checks:

- `python -m py_compile backend\app\schemas\common.py backend\app\services\clinical_readiness_preview.py` - proslo
- `npm run typecheck` - proslo
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_preview.py` - proslo, 19 passed
- `npm run smoke` - proslo

Zavrsni full regression pass biljezi se u finalnom odgovoru ovog taska.

## Remaining risks

- snapshot nije implementiran
- nema immutable zapisa previewa
- nema persistence modela
- nema audit capture workflowa
- nema snapshot history UI-ja
- nema decision governancea
- nema production readinessa

## Go / No-Go

Go za nastavak demo/pilot transparency razvoja.

No-Go za snapshot persistence, capture endpoint, Outcome Evidence, enforcement, override, Task engine, real AI/OCR i stvarne podatke dok se posebno ne odobri sljedeca faza.

## Recommended next task

`Program 1 Phase B9 - Clinical Readiness Snapshot Persistence Design`

Razlog:

Prije implementacije persistencea ASTRA mora definirati schema shape, audit event, immutability pravila, capture akciju i relation prema appointmentu, template versionu i source-linked Patient Clinical Knowledge.
