# Program 1 Phase B3 - Regression Notes

Status: implementation regression notes

## Implemented

Phase B3 uvodi najmanji sigurni Clinical Readiness read-only preview.

Implementirano:

- read-only appointment-scoped preview endpoint
- deterministic preview service
- Appointment Workspace preview section
- regression tests
- smoke coverage

Endpoint:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

Preview je:

- appointment-scoped
- read-only
- non-blocking
- demo/pilot-only
- odvojen od `/api/readiness`

## Not implemented

B3 nije implementirao:

- Clinical Readiness enforcement
- blocking workflow
- Task engine
- override
- AI clearance
- real AI/OCR
- real patient data
- production/certification claims
- database models
- migrations
- service-specific readiness templates
- Outcome Evidence
- Episode-Based Care kao primarni workflow

## Safety properties

B3 preview:

- ne mijenja appointment status
- ne kreira task
- ne kreira episode
- ne kreira ClinicalPlan
- ne kreira Outcome Evidence
- ne auditira obican read
- ne zahtijeva Clinical Episode
- ne koristi unreviewed AI extraction kao official source
- ne koristi Patient Clinical Summary kao source of truth
- prikazuje Open Questions samo kao warning/physician-review iteme

## Tests/checks

Izvedeni B3 regression gate:

- `docker compose build backend` - proslo
- `docker compose run --rm --entrypoint python -e PYTHONPATH=/app backend -m py_compile app/main.py app/api/routes/appointments.py app/services/clinical_readiness_preview.py` - proslo
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend tests/test_clinical_readiness_preview.py` - proslo, 9 passed
- `docker compose run --rm --entrypoint pytest -e PYTHONPATH=/app backend` - proslo, 154 passed, 9 skipped
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router bundler warninge
- `npm run smoke` - proslo

Napomena:

Standardni `docker compose run --rm -e PYTHONPATH=/app backend pytest` pokusaj nije dosao do testova jer lokalni Postgres Docker volume ima staru `alembic_version` kolonu prekratku za naziv migracije `0011_reception_resource_scheduling`. Testovi su zato pokrenuti kroz isti backend image s pytest entrypointom, koji koristi izoliranu SQLite test bazu kao postojece backend unit test fixturee.

## Remaining risks

- preview je deterministicki i ogranicen
- nema service-specific readiness templates
- nema override governance
- nema task integration
- nema real production readiness
- clinical readiness statusi jos nisu persistentni
- source badge UI za preview je tekstualan, ne poseban badge component

## Recommended next task

`Program 1 Phase B4 - Clinical Readiness Template Design`

Razlog:

Preview sada postoji kao read-only surface, ali nema sigurni service-specific template model. Prije hardeninga UI-ja ili bilo kakvog enforcementa treba definirati template design.
