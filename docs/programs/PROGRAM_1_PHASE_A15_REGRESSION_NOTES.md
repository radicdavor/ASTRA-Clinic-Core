# Program 1 - Phase A15 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A15 - Split Patient Routes.

A15 je route modularization pass za Patient API. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- Dodan je `backend/app/api/routes/patients.py`.
- Patient CRUD i patient child endpointi su premjesteni iz `core.py` u zaseban route modul.
- `backend/app/main.py` registrira `patients.router`.
- Patient duplicate check ostaje na istom URL-u.
- Frontend smoke provjera cuva da novi route modul sadrzi Patient URL contract.

Endpoint URL-ovi ostaju isti:

- `POST /api/patients`
- `GET /api/patients`
- `GET /api/patients/possible-duplicates`
- `GET /api/patients/{patient_id}`
- `GET /api/patients/{patient_id}/appointments`
- `GET /api/patients/{patient_id}/episodes`
- `GET /api/patients/{patient_id}/invoices`
- `PATCH /api/patients/{patient_id}`

## 3. Namjerno nije implementirano

- novi patient identity model
- novi duplicate resolution workflow
- real-data odobrenje
- Clinical Readiness Gate
- Task engine
- Workflow Engine
- Episode-Based Care kao primary workflow
- nove tablice ili migracije
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Regression checks

Za A15 treba pokrenuti:

- `python -m py_compile app\main.py app\api\routes\core.py app\api\routes\patients.py` - proslo
- `git diff --check` - proslo
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router warninge
- `npm run smoke` - proslo

Backend `pytest` ostaje ovisan o podrzanom Python runtimeu ili Dockeru jer lokalni Python 3.14 ne moze instalirati zakljucani `psycopg-binary==3.2.3`.

## 5. Preostali rizici

- `core.py` i dalje sadrzi appointment, reception, episode, catalog, search i audit rute.
- Patient child endpointi i dalje presijecaju appointment/episode/billing domene, ali URL ugovor je sacuvan.
- Backend pytest nije lokalno izvrsiv u trenutnom Python 3.14 runtimeu.

## 6. Preporuceni sljedeci zadatak

`Program 1 Phase A16 - Split Appointment and Reception Routes`

Razlog: appointment/reception je sljedeci veliki operativni blok u `core.py`, ali ga treba razdvojiti pazljivo zbog shared appointment helpera i status workflowa.
