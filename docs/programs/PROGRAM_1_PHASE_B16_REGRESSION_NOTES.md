# Program 1 Phase B16 - Regression Notes

Status: backend read API prototype, no frontend UI

## Implemented

B16 dodaje read-only backend API za appointment-scoped Clinical Readiness Snapshot history.

Implementirano:

- snapshot history response schemas
- backend read endpoint:

  `GET /api/appointments/{appointment_id}/clinical-readiness-snapshots`

- read permission requirement:

  `clinical_readiness.snapshots.read`

- summary-only history list
- newest-first sorting
- preview-only warning
- regression coverage

History list prikazuje samo summary fields:

- snapshot id
- appointment/patient/service id
- created by user id
- created/preview timestamps
- preview status
- template metadata
- snapshot reason
- preview-only flag
- disclaimer
- item/limitation/source-warning counts
- supersession metadata

## Behavioral changes

Dodana je nova backend read ruta za pregled snapshot historyja.

Nema frontend UI promjene.

Nema capture buttona.

Nema snapshot detail endpointa.

## API compatibility

Novi endpoint:

`GET /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Zahtjevi:

- authenticated user
- permission `clinical_readiness.snapshots.read`

Endpoint je read-only i appointment-scoped.

Postojeci capture endpoint ostaje:

`POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Capture i dalje zahtijeva `clinical_readiness.snapshots.write`.

## Safety properties

B16 cuva sljedece granice:

- history read ne stvara snapshot
- history read ne pise audit by default
- history read ne mijenja appointment status
- history read ne stvara Task
- history read ne stvara Outcome Evidence
- history read ne stvara ClinicalPlan
- history read ne stvara ClinicalEpisode
- response ne sadrzi approval/clearance fields
- list response ne izlaže raw `items_json`
- warning jasno kaze da snapshot history nije clinical approval ili readiness clearance

## Not implemented

B16 nije implementirao:

- frontend history UI
- frontend capture button
- snapshot detail endpoint
- snapshot detail UI
- snapshot delete/edit
- supersession UI
- Outcome Evidence
- Task engine
- override
- appointment status change
- clinical approval
- patient messaging
- real AI/OCR
- real patient data

## Remaining risks

- no frontend history surface yet
- no capture reason modal yet
- no snapshot detail endpoint
- no supersession UX
- production governance is incomplete

## Go / No-Go

Go za sljedeci read-only UI korak:

`Program 1 Phase B17 - Snapshot History UI Read-Only Surface`

No-Go za:

- capture button bez posebnog odobrenja
- edit/delete snapshot
- clinical approval
- override workflow
- Task engine
- Outcome Evidence
- appointment status change

## Recommended next task

`Program 1 Phase B17 - Snapshot History UI Read-Only Surface`

B17 treba dodati samo read-only UI prikaz. Capture button ostaje izvan scopea dok history display nije stabilan i posebno odobren.
