# Program 1 Phase B15 - Regression Notes

Status: backend endpoint prototype, no frontend UI

## Implemented

B15 izlaže interni B14 capture service kroz usko ogranicen backend endpoint.

Implementirano:

- capture request schema
- capture response schema
- backend endpoint:

  `POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`

- route-level permission requirement:

  `clinical_readiness.snapshots.write`

- reason-required capture
- explicit denial of API key capture
- audit-backed service call
- endpoint regression coverage

Endpoint vraca samo safe snapshot fields:

- id
- appointment id
- patient id
- service id
- created at
- created by user id
- schema version
- preview generated at
- preview status
- template key/label/version
- template binding status
- snapshot reason
- preview-only flag
- disclaimer
- items
- limitations
- source warnings
- source refs

## Behavioral changes

Dodana je nova backend write ruta za eksplicitni snapshot capture.

Nema frontend UI promjene.

Nema capture buttona.

Nema snapshot history UI-ja.

## API compatibility

Novi endpoint:

`POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Zahtjevi:

- authenticated user
- permission `clinical_readiness.snapshots.write`
- non-empty `reason`

API key capture je odbijen iako API key ima snapshot scope.

Request ne prihvaca client preview payload.

Postojeci preview endpoint ostaje read-only:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

## Safety properties

B15 cuva sljedece granice:

- endpoint je permission-gated
- endpoint zahtijeva reason
- endpoint rebuilda server-side preview kroz service
- endpoint ne vjeruje client preview payloadu
- endpoint sprema preview-only snapshot
- endpoint pise audit event kroz service
- endpoint ne mijenja appointment status
- endpoint ne stvara Task
- endpoint ne stvara Outcome Evidence
- endpoint ne stvara ClinicalPlan
- endpoint ne stvara ClinicalEpisode
- endpoint ne salje patient message
- endpoint ne radi override
- response ne sadrzi `approved`, `cleared`, `procedure_allowed`, `task_created`, `outcome_evidence_id` ili `override_status`

## Not implemented

B15 nije implementirao:

- frontend capture UI
- capture button
- snapshot history UI
- supersession UI
- Outcome Evidence
- Task engine
- override
- appointment status change
- patient messaging
- real AI/OCR
- real patient data
- production/certification claim

## Remaining risks

- no frontend capture workflow yet
- no user-facing reason modal yet
- no snapshot history UI yet
- no supersession UX
- permission seed/admin UX remains minimal
- idempotency persistence remains deferred
- production governance is not complete

## Go / No-Go

Go za sljedeci read/history API korak:

`Program 1 Phase B16 - Snapshot History Read API Prototype`

No-Go za:

- frontend capture button prije history surfacea
- clinical approval
- override workflow
- Task engine
- Outcome Evidence
- appointment status change

## Recommended next task

`Program 1 Phase B16 - Snapshot History Read API Prototype`

Razlog:

Prije dodavanja capture buttona korisnici trebaju siguran read/history prikaz vec spremljenih snapshotova.
