# Program 1 - Phase A10 Core Route Domain Split Plan

## 1. Svrha

Ovaj dokument definira siguran plan razdvajanja `backend/app/api/routes/core.py` nakon A9 modularizacijskog passa.

A10 nije implementacija nove klinicke funkcionalnosti. A10 je arhitektonski plan za postupno razdvajanje route modula uz ocuvanje postojecih URL-ova, API ugovora i Phase A8 regression gate invariants.

Ovaj dokument nije:

- produkcijsko odobrenje
- real-data odobrenje
- compliance odobrenje
- tvrdnja da je ASTRA certificirani EMR
- tvrdnja da je ASTRA medicinski uredaj

ASTRA ostaje demo/pilot sustav. Stvarni pacijentovi podaci nisu dopusteni.

## 2. Zasticeni invariants

Svaki route split mora sacuvati:

1. `ClinicalDocument` kao source object.
2. AI extraction kao prijedlog, ne sluzbenu istinu.
3. Official Patient Clinical Knowledge samo iz reviewed source documents.
4. `PatientClinicalSummaryRecord` kao summary view, ne source of truth.
5. Open Questions kao source-linked warnings, ne taskove.
6. Clinical Evidence Timeline kao read-only audit view.
7. Operational Readiness odvojeno od buduceg Clinical Readiness Gatea.
8. Episode-Based Care kao deferred/compatibility povrsinu.
9. Nema real AI/OCR providera.
10. Nema stvarnih pacijentovih podataka.

## 3. Trenutno stanje nakon A9

`core.py` je smanjen, ali i dalje sadrzi vise route domena:

- public/system config
- Operational Readiness
- episode compatibility/deferred route
- clinical plan route
- clinical document route
- patient clinical summary route
- patient route
- appointment/schedule route
- reception route
- search route
- services/clinics/providers/rooms/modules route
- audit-log route

A9 je vec premjestio:

- ClinicalDocument helper logiku u `backend/app/services/clinical_documents.py`
- Operational Readiness builder u `backend/app/services/readiness.py`

## 4. Predlozene route granice

### 4.1 System routes

Predlozeni modul:

`backend/app/api/routes/system.py`

Sadrzi:

- `GET /api/public-config`

Rizik: nizak.

### 4.2 Operational Readiness routes

Predlozeni modul:

`backend/app/api/routes/readiness.py`

Sadrzi:

- `GET /api/readiness`

Rizik: nizak jer je builder vec izdvojen u servis.

Ovo je najbolji prvi stvarni route split nakon A10.

### 4.3 Clinical Documents routes

Predlozeni modul:

`backend/app/api/routes/clinical_documents.py`

Sadrzi:

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

Rizik: srednji. Ovaj split treba napraviti tek nakon readiness/system split-a i nakon prolaska smoke provjera.

### 4.4 Patient Knowledge Summary routes

Predlozeni modul:

`backend/app/api/routes/patient_knowledge.py`

Sadrzi:

- `GET /api/patients/{patient_id}/clinical-summary`
- `POST /api/patients/{patient_id}/clinical-summary/generate-draft`
- `PATCH /api/patients/{patient_id}/clinical-summary`
- `POST /api/patients/{patient_id}/clinical-summary/review`

Rizik: srednji jer su semantics blisko vezane uz ClinicalDocument.

Preporuka: razdvojiti zajedno s ili odmah nakon ClinicalDocuments route split-a.

### 4.5 Patient routes

Predlozeni modul:

`backend/app/api/routes/patients.py`

Sadrzi:

- `POST /api/patients`
- `GET /api/patients`
- `GET /api/patients/possible-duplicates`
- `GET /api/patients/{patient_id}`
- `GET /api/patients/{patient_id}/appointments`
- `GET /api/patients/{patient_id}/episodes`
- `GET /api/patients/{patient_id}/invoices`
- `PATCH /api/patients/{patient_id}`

Rizik: srednji jer postoje cross-domain child resources.

### 4.6 Appointment and reception routes

Predlozeni moduli:

- `backend/app/api/routes/appointments.py`
- `backend/app/api/routes/reception.py`

Appointment sadrzi CRUD i schedule:

- `POST /api/appointments`
- `GET /api/appointments`
- `GET /api/appointments/{appointment_id}`
- `PATCH /api/appointments/{appointment_id}`
- `DELETE /api/appointments/{appointment_id}`
- `GET /api/schedule/day`

Reception sadrzi:

- `GET /api/reception/day`
- `POST /api/appointments/{appointment_id}/mark-arrived`

Rizik: srednji zbog shared appointment helpera i appointment validationa.

### 4.7 Deferred episode/clinical plan routes

Predlozeni modul:

`backend/app/api/routes/episodes.py`

Sadrzi episode i clinical plan compatibility rute.

Rizik: srednji. Buduci da je Episode-Based Care deferred, split ne smije reaktivirati episode-first workflow.

### 4.8 Catalog and audit routes

Predlozeni moduli:

- `backend/app/api/routes/catalog.py`
- `backend/app/api/routes/audit.py`

Catalog:

- services
- clinics
- modules
- providers
- rooms
- search ako ostane globalan

Audit:

- `GET /api/audit-log`

Rizik: nizak do srednji.

## 5. Redoslijed implementacije

Preporuceni redoslijed:

1. A11 - Split Operational Readiness route
2. A12 - Split System/Public Config route
3. A13 - Split ClinicalDocument routes
4. A14 - Split Patient Clinical Summary routes
5. A15 - Split Patient routes
6. A16 - Split Appointment and Reception routes
7. A17 - Split Deferred Episode/ClinicalPlan routes
8. A18 - Split Catalog and Audit routes
9. A19 - Remove remaining generic `core.py` or rename it to the last real domain

Svaki korak mora biti mali i reverzibilan.

## 6. Test strategy

Svaki split mora pokrenuti barem:

- `git diff --check`
- Python syntax/import check
- backend targeted pytest kada je podrzan Python runtime dostupan
- `npm run typecheck`
- `npm run build`
- `npm run smoke`

Smoke mora biti azuriran ako prestane traziti tekst u `core.py` i treba traziti isti contract u novom route/servisnom modulu.

## 7. No-Go

Route split ne smije:

- mijenjati URL-ove
- mijenjati response modele
- dodati migracije
- dodati nove tablice
- uvoditi Task engine
- uvoditi Clinical Readiness Gate
- reaktivirati Episode-Based Care
- uvoditi real AI/OCR
- dodati stvarne pacijentove podatke
- dodati produkcijske ili certifikacijske tvrdnje

## 8. Preporuceni sljedeci zadatak

`Program 1 Phase A11 - Split Operational Readiness Route`

Razlog: readiness logika je vec u `backend/app/services/readiness.py`, pa route modul moze postati tanak i samostalan uz najmanji rizik.

## 9. A11 implementation update

A11 je implementirao prvi stvarni route split:

- `GET /api/readiness` je premjesten u `backend/app/api/routes/readiness.py`.
- `backend/app/main.py` registrira `readiness.router`.
- `backend/app/services/readiness.py` ostaje canonical Operational Readiness builder.
- URL i API ugovor ostaju isti.

Preporuceni sljedeci zadatak nakon A11:

`Program 1 Phase A12 - Split System Public Config Route`

## 10. A12 implementation update

A12 je implementirao drugi niskorizicni route split:

- `GET /api/public-config` je premjesten u `backend/app/api/routes/system.py`.
- `backend/app/main.py` registrira `system.router`.
- URL i API ugovor ostaju isti.

Preporuceni sljedeci zadatak nakon A12:

`Program 1 Phase A13 - Split ClinicalDocument Routes`
