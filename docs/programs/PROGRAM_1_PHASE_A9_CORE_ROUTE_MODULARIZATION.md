# Program 1 - Phase A9 Core Route Modularization Pass

## 1. Svrha

Ovaj dokument opisuje uski A9 modularizacijski pass nakon Phase A8 regression gatea.

Svrha A9 nije dodavanje nove klinicke funkcionalnosti. Svrha je smanjiti rizik u prevelikom `core.py` route modulu i premjestiti stabilnu pomocnu logiku u servisne module.

Ovaj pass nije:

- produkcijsko odobrenje
- real-data odobrenje
- compliance odobrenje
- tvrdnja da je ASTRA certificirani EMR
- tvrdnja da je ASTRA medicinski uredaj

ASTRA i dalje ostaje demo/pilot sustav. Stvarni pacijentovi podaci nisu dopusteni.

## 2. Zasticeni invariants

A9 mora sacuvati sve Phase A8 regression gate invariants:

1. `ClinicalDocument` ostaje source object.
2. AI extraction ostaje prijedlog, ne sluzbena istina.
3. Official Patient Clinical Knowledge zahtijeva reviewed source documents.
4. `PatientClinicalSummaryRecord` ostaje summary view, ne source of truth.
5. Open Questions ostaju source-linked warnings, ne taskovi.
6. Clinical Evidence Timeline ostaje read-only audit view.
7. Operational Readiness nije Clinical Readiness Gate.
8. Episode-Based Care ostaje deferred.
9. Nema real AI/OCR providera.
10. Nema stvarnih pacijentovih podataka.

## 3. Sto je modularizirano

A9 izdvaja pomocnu logiku iz `backend/app/api/routes/core.py` u servisni sloj:

- `backend/app/services/clinical_documents.py`
  - dohvat ClinicalDocumenta ili 404
  - validacija patient/appointment linka za dokument
  - deterministic AI extraction placeholder helper
  - ClinicalDocument review/extraction lifecycle helperi

- `backend/app/services/readiness.py`
  - izgradnja Operational Readiness odgovora
  - readiness count/helper logika
  - Patient Summary stale readiness provjera
  - Episode Engine deferred readiness poruka

Endpointi ostaju isti.

API ugovor ostaje isti.

Nema migracija.

Nema novih tablica.

## 4. Sto namjerno nije modularizirano

U ovom passu nisu premjesteni svi route blokovi iz `core.py`.

Razlog: sigurniji je inkrementalni pristup. ClinicalDocument i readiness helperi imaju dobru regresijsku zastitu iz A8 i mogu se premjestiti bez promjene URL-ova ili frontend ugovora.

Preostale odgovornosti u `core.py` ukljucuju:

- patient rute
- appointment rute
- episode compatibility/deferred rute
- clinical plan compatibility rute
- reception rute
- services/providers/rooms/modules/audit rute

Buduci pass moze razmotriti razdvajanje route modula po domenama, ali samo ako A8 gate ostane zelen.

## 5. Regression gate nakon A9

Minimalne provjere nakon A9:

- `git diff --check`
- backend syntax/import check
- backend Phase A gate testovi kada je podrzana Python verzija dostupna
- frontend typecheck
- frontend build
- frontend smoke

Ako lokalno okruzenje nema podrzanu Python verziju za zakljucane dependencyje, backend pytest treba pokrenuti kroz podrzani runtime ili Docker.

## 6. No-Go

A9 ne smije uvesti:

- Task engine
- Clinical Readiness Gate
- Episode-Based Care kao primary workflow
- Workflow Engine
- Outcome Evidence object
- real AI provider
- real OCR provider
- stvarne pacijentove podatke
- produkcijske ili certifikacijske tvrdnje

## 7. Preporuceni sljedeci korak

Nakon A9 preporuceni sljedeci korak je:

`Program 1 Phase A10 - Core Route Domain Split Plan`

Taj korak treba odluciti hoce li se stvarno razdvajati FastAPI route moduli po domenama ili ce se nastaviti servisna ekstrakcija bez promjene router strukture.
