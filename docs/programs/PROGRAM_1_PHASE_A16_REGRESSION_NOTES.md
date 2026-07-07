# Program 1 Phase A16 - Regression Notes

## Sto je implementirano

A16 je izdvojio appointment i reception rute iz preostalog `core.py` bez promjene javnih API adresa.

Implementirano:

- novi `backend/app/api/routes/appointments.py`
- novi `backend/app/api/routes/reception.py`
- registracija `appointments.router` i `reception.router` u `backend/app/main.py`
- smoke provjere za nove route module
- dokumentiran A16 route split i ozicenje

`core.py` je smanjen s fokusom na preostale episode/clinical plan, search/catalog i audit rute koje jos nisu izdvojene.

## Zadrzani API ugovor

Bez promjene ostaju:

- `POST /api/appointments`
- `GET /api/appointments`
- `GET /api/appointments/{appointment_id}`
- `PATCH /api/appointments/{appointment_id}`
- `DELETE /api/appointments/{appointment_id}`
- `GET /api/schedule/day`
- `GET /api/reception/day`
- `POST /api/appointments/{appointment_id}/mark-arrived`

Frontend ne mijenja adrese.

## Sto nije implementirano

A16 nije uveo:

- Clinical Readiness Gate
- Task engine
- Workflow Engine
- Outcome Evidence objekt
- Episode-Based Care kao primarni workflow
- stvarni AI provider
- stvarni OCR provider
- stvarne podatke pacijenata
- produkcijske ili certifikacijske tvrdnje

Episode Engine ostaje eksperimentalno/deferred. Termini i dalje mogu postojati bez epizode.

## Testovi

Izvedeni A16 regression gate:

- `python -m py_compile app/main.py app/api/routes/appointments.py app/api/routes/reception.py app/api/routes/core.py` - proslo
- `docker compose run --rm -e PYTHONPATH=/app backend pytest` - proslo, 87 passed, 9 skipped
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router bundler warninge
- `npm run smoke` - proslo
- `git diff --check` - proslo

Napomena: `docker compose run --rm backend pytest` bez eksplicitnog `PYTHONPATH=/app` pao je prije testova s `ModuleNotFoundError: No module named 'app'`. Podrzani Docker test run je zato izveden s eksplicitnim `PYTHONPATH=/app`.

## Preostali rizici

- `core.py` i dalje sadrzi episode/clinical plan, search/catalog i audit rute.
- `inventory.py` i dalje sadrzi appointment-bound material/invoice endpointove jer pripadaju inventory/billing kontekstu; to je prihvatljivo za A16.
- Backend full test suite mora proci u podrzanom runtimeu prije nastavka sljedece faze.

## Go / No-Go

Go za A16 ako backend testovi, frontend typecheck/build/smoke i `git diff --check` prodju.

No-Go ako:

- bilo koja stara appointment/reception API adresa nestane
- reception arrival audit promijeni znacenje
- readiness pocne glumiti Clinical Readiness Gate
- Episode Engine postane obavezan za termine

## Preporuceni sljedeci task

`Program 1 Phase A17 - Split Episode and Clinical Plan Routes`

Razlog: `core.py` nakon A16 jos uvijek nosi veliki deferred Episode/ClinicalPlan blok. Izdvajanje tog bloka treba ostati arhitektonsko ciscenje, bez reaktivacije Episode-Based Care kao primarnog workflowa.
