# Program 1 - Phase A11 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A11 - Split Operational Readiness Route.

A11 je prvi stvarni route domain split nakon A10 plana. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- Dodan je `backend/app/api/routes/readiness.py`.
- `GET /api/readiness` je premjesten iz `core.py` u novi readiness route modul.
- `backend/app/main.py` registrira `readiness.router`.
- `backend/app/services/readiness.py` i dalje sadrzi Operational Readiness builder.
- Frontend smoke provjera sada cuva:
  - da novi readiness route modul sadrzi `/readiness`
  - da `main.py` registrira `readiness.router`
  - da readiness contract i dalje zivi u `services/readiness.py`

Endpoint URL ostaje isti:

- `GET /api/readiness`

## 3. Namjerno nije implementirano

- Clinical Readiness Gate
- Task engine
- Workflow Engine
- Outcome Evidence object
- Episode-Based Care kao primary workflow
- real AI provider
- real OCR provider
- nove tablice ili migracije
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Regression checks

Za A11 treba pokrenuti:

- `python -m py_compile app\main.py app\api\routes\core.py app\api\routes\readiness.py app\services\readiness.py` - proslo
- `git diff --check` - proslo
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router warninge
- `npm run smoke` - proslo

Backend `pytest` ostaje ovisan o podrzanom Python runtimeu ili Dockeru jer lokalni Python 3.14 ne moze instalirati zakljucani `psycopg-binary==3.2.3`.

## 5. Preostali rizici

- `core.py` je dodatno smanjen, ali i dalje sadrzi vecinu domena.
- ClinicalDocument route split je veci rizik i treba ga napraviti tek uz A8/A11 smoke coverage.
- Public config route jos je u `core.py`.

## 6. Go/No-Go

Go za A11 route split.

No-Go za sirenje prema Clinical Readiness Gateu, Task engineu, Workflow Engineu ili Episode-Based Careu bez posebne odluke.

## 7. Preporuceni sljedeci zadatak

`Program 1 Phase A12 - Split System Public Config Route`

Razlog: `GET /api/public-config` je nizak rizik, sistemski endpoint i moze se izdvojiti bez utjecaja na klinički tok.
