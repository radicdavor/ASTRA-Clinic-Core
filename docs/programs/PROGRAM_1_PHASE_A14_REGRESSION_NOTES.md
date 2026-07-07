# Program 1 - Phase A14 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A14 - Split Patient Clinical Summary Routes.

A14 je route modularization pass za Patient Clinical Summary. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- Dodan je `backend/app/api/routes/patient_clinical_summary.py`.
- Patient Clinical Summary endpointi su premjesteni iz `core.py` u zaseban route modul.
- `backend/app/main.py` registrira `patient_clinical_summary.router`.
- Summary i dalje ostaje pomocni view.
- Official Patient Clinical Knowledge i dalje dolazi iz reviewed, source-linked ClinicalDocument izvora.
- Frontend smoke provjera cuva da novi route modul sadrzi clinical-summary URL contract.

Endpoint URL-ovi ostaju isti:

- `GET /api/patients/{patient_id}/clinical-summary`
- `POST /api/patients/{patient_id}/clinical-summary/generate-draft`
- `PATCH /api/patients/{patient_id}/clinical-summary`
- `POST /api/patients/{patient_id}/clinical-summary/review`

## 3. Namjerno nije implementirano

- novi source of truth za summary
- formalni Finding object
- Task engine
- Clinical Readiness Gate
- Workflow Engine
- Episode-Based Care kao primary workflow
- real AI provider
- real OCR provider
- nove tablice ili migracije
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Regression checks

Za A14 treba pokrenuti:

- `python -m py_compile app\main.py app\api\routes\core.py app\api\routes\patient_clinical_summary.py` - proslo
- `git diff --check` - proslo
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router warninge
- `npm run smoke` - proslo

Backend `pytest` ostaje ovisan o podrzanom Python runtimeu ili Dockeru jer lokalni Python 3.14 ne moze instalirati zakljucani `psycopg-binary==3.2.3`.

## 5. Preostali rizici

- `core.py` i dalje sadrzi patient, appointment, reception, episode, catalog i audit rute.
- Backend pytest nije lokalno izvrsiv u trenutnom Python 3.14 runtimeu.
- Sljedeci route split mora i dalje cuvati Patient Knowledge invariants.

## 6. Preporuceni sljedeci zadatak

`Program 1 Phase A15 - Split Patient Routes`

Razlog: patient route blok je sljedeci stabilni, jasni domain split nakon ClinicalDocument i Patient Clinical Summary modula.
