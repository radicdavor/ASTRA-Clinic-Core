# Program 1 Phase A17 - Regression Notes

## Implemented

A17 je izdvojio Episode i ClinicalPlan route handlere iz `backend/app/api/routes/core.py` u:

`backend/app/api/routes/episodes.py`

Implementirano:

- episode list/create/detail/update/close rute izdvojene su u `episodes.py`
- episode appointments ruta izdvojena je u `episodes.py`
- clinical plan generate/list/active/edit/reject/confirm rute izdvojene su u `episodes.py`
- episode clinical decision timeline izdvojen je u `episodes.py`
- `episodes.router` je registriran u `backend/app/main.py`
- smoke provjera cuva prisutnost novog route modula
- `core.py` je dodatno smanjen i sada zadrzava catalog/search/audit rute za A18

Nije planirana korisnicka promjena ponasanja. Ovo je route modularizacija.

## API paths preserved

Bez promjene ostaju:

- `GET /api/episodes`
- `POST /api/episodes`
- `GET /api/episodes/{episode_id}`
- `PATCH /api/episodes/{episode_id}`
- `POST /api/episodes/{episode_id}/close`
- `GET /api/episodes/{episode_id}/appointments`
- `GET /api/episodes/{episode_id}/clinical-plans`
- `GET /api/episodes/{episode_id}/clinical-plans/active`
- `POST /api/episodes/{episode_id}/clinical-plans/generate`
- `PATCH /api/clinical-plans/{plan_id}`
- `POST /api/clinical-plans/{plan_id}/reject`
- `POST /api/clinical-plans/{plan_id}/confirm`
- `GET /api/episodes/{episode_id}/clinical-timeline`

`GET /api/patients/{patient_id}/episodes` ostaje u `patients.py` jer pripada Patient Workspace kontekstu.

## Not implemented

A17 nije uveo:

- Episode-Based Care kao primarni workflow
- Task engine
- Clinical Readiness Gate
- Workflow Engine
- Outcome Evidence objekt
- Medical Note formal output
- Patient Explanation formal output
- Consent lifecycle
- Procedure/Treatment templates
- real AI provider
- real OCR provider
- stvarne podatke pacijenata
- produkcijske ili certifikacijske tvrdnje
- migracije baze

Episode Workspace ostaje experimental/deferred compatibility surface. ClinicalPlan ostaje episode-bound suggestion/confirmation objekt, ne Workflow Engine.

## Tests/checks

Izvedeni A17 regression gate:

- `git diff --check` - proslo
- `python -m py_compile app/main.py app/api/routes/episodes.py app/api/routes/core.py` - proslo
- `docker compose run --rm -e PYTHONPATH=/app backend pytest` - proslo, 87 passed, 9 skipped
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router bundler warninge
- `npm run smoke` - proslo

`make test` nije pokrenut jer `make` nije dostupan u ovom Windows okruzenju. Ekvivalentne provjere su pokrenute rucno.

## Remaining risks

- `core.py` jos sadrzi catalog/search/audit rute.
- Episode Engine ostaje deferred i ne smije se tretirati kao primarni klinicki workflow.
- ClinicalPlan ostaje placeholder/suggestion-confirmation objekt, ne task/workflow engine.
- Future service-layer extraction za episode helper logiku moze biti korisna, ali nije potrebna za A17.

## Go / No-Go

Go za A17 ako backend testovi, frontend typecheck/build/smoke i `git diff --check` prodju.

No-Go ako:

- bilo koja episode/clinical plan API adresa nestane
- permissions ili response schema promijene behavior
- ClinicalPlan pocne mijenjati epizodu bez lijecnicke potvrde
- readiness pocne tretirati nedostatak epizode kao blocker
- Episode Engine postane primarni workflow

## Recommended next task

`Program 1 Phase A18 - Split Catalog, Search and Audit Routes`

Razlog: nakon A17 `core.py` je mali, ali jos uvijek sluzi kao privremeni modul za search, catalog i audit rute. A18 moze zatvoriti route modularization pass bez uvodjenja novih klinickih funkcionalnosti.
