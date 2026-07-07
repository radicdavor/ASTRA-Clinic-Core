# Program 1 - Phase A13 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A13 - Split ClinicalDocument Routes.

A13 je route modularization pass. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- Dodan je `backend/app/api/routes/clinical_documents.py`.
- ClinicalDocument route blok je premjesten iz `core.py` u zaseban route modul.
- `backend/app/main.py` registrira `clinical_documents.router`.
- ClinicalDocument helper logika ostaje u `backend/app/services/clinical_documents.py`.
- Clinical Evidence Timeline endpoint ostaje read-only i premjesten je zajedno s dokumentom.
- Patient Clinical Summary endpointi ostaju u `core.py` i nisu mijenjani u ovom passu.
- Frontend smoke provjera cuva da novi route modul sadrzi ClinicalDocument URL contract.

Endpoint URL-ovi ostaju isti:

- `GET /api/clinical-documents`
- `POST /api/clinical-documents`
- `POST /api/patients/{patient_id}/clinical-documents`
- `POST /api/clinical-documents/upload`
- `GET /api/clinical-documents/search`
- `GET /api/clinical-documents/{document_id}`
- `GET /api/clinical-documents/{document_id}/evidence-timeline`
- `PATCH /api/clinical-documents/{document_id}`
- `POST /api/clinical-documents/{document_id}/extract`
- `POST /api/clinical-documents/{document_id}/review`
- `POST /api/clinical-documents/{document_id}/reject-summary`
- `GET /api/patients/{patient_id}/clinical-documents`

## 3. Namjerno nije implementirano

- Patient Clinical Summary route split
- formalni Finding object
- real AI provider
- real OCR provider
- Task engine
- Clinical Readiness Gate
- Workflow Engine
- Episode-Based Care kao primary workflow
- nove tablice ili migracije
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Regression checks

Za A13 treba pokrenuti:

- `python -m py_compile app\main.py app\api\routes\core.py app\api\routes\clinical_documents.py app\services\clinical_documents.py` - proslo
- `git diff --check` - proslo
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router warninge
- `npm run smoke` - proslo

Backend `pytest` ostaje ovisan o podrzanom Python runtimeu ili Dockeru jer lokalni Python 3.14 ne moze instalirati zakljucani `psycopg-binary==3.2.3`.

## 5. Preostali rizici

- `core.py` i dalje sadrzi patient summary, patient, appointment, reception, episode, catalog i audit rute.
- Patient Clinical Summary je semanticki vezan uz ClinicalDocument i treba zaseban A14 split s oprezom.
- Backend pytest nije lokalno izvrsiv u trenutnom Python 3.14 runtimeu.

## 6. Preporuceni sljedeci zadatak

`Program 1 Phase A14 - Split Patient Clinical Summary Routes`

Razlog: summary endpointi su sljedeci logicki klinicki knowledge blok, ali moraju ostati summary view, ne source of truth.
