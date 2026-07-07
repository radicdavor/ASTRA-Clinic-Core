# Program 1 Phase B14 - Regression Notes

Status: backend service prototype, no endpoint, no UI

## Implemented

B14 dodaje interni service-layer prototype za Clinical Readiness Snapshot capture.

Implementirano:

- snapshot capture service
- server-side rebuild postojeceg Clinical Readiness Previewa
- immutable copied preview payload persistence
- service-level audit integration
- atomic snapshot save + audit write
- regression coverage za capture service

Servis sprema:

- appointment id
- patient id
- service id
- created by user id
- schema version
- preview generated timestamp
- preview status
- preview summary
- template key/label/version
- template binding status/warning
- reason
- preview-only flag
- items JSON
- limitations JSON
- source warnings JSON
- source refs JSON
- disclaimer

Audit event:

`clinical_readiness_snapshot_captured`

## Behavioral changes

Runtime API i UI se ne mijenjaju.

Nema javne rute za capture.

Nema frontend capture buttona.

Postoji samo interni backend service koji buduca B15 faza moze izloziti kroz usko permission-gated endpoint.

## API compatibility

Nema novih API path promjena.

Postojeci endpoint ostaje read-only:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

Preview GET i dalje:

- ne stvara snapshot
- ne pise audit
- ne mijenja appointment status
- ne stvara workflow objekte

## Safety properties

B14 cuva sljedece granice:

- capture service zahtijeva non-empty reason
- capture service zahtijeva actor user id
- capture service rebuilda server-side preview
- client preview payload se ne prihvaca
- snapshot ostaje preview-only
- audit event ne znaci clinical approval
- audit i snapshot se spremaju u istoj transakciji
- audit failure rollbacka snapshot
- Patient Clinical Summary nije source of truth
- unreviewed AI nije official source
- appointment status se ne mijenja
- Task se ne stvara
- Outcome Evidence se ne stvara
- ClinicalPlan se ne stvara
- ClinicalEpisode se ne stvara

## Not implemented

B14 nije implementirao:

- capture endpoint
- frontend capture UI
- capture button
- snapshot history UI
- route-level permission enforcement
- idempotency persistence
- supersession behavior
- Outcome Evidence
- Task engine
- override
- appointment status change
- patient messaging
- real AI/OCR
- real patient data
- production/certification claim

## Remaining risks

- no public endpoint yet
- route-level permission still not enforced
- no UI reason flow
- no snapshot history UI
- no supersession UX
- idempotency remains deferred because B13 did not add idempotency storage
- production governance is not complete

## Go / No-Go

Go za sljedeci uski backend API korak:

`Program 1 Phase B15 - Snapshot Capture Endpoint Prototype`

No-Go za:

- frontend capture button
- snapshot history UI prije read API-ja
- endpoint bez permission enforcementa
- endpoint bez required reasona
- audit-free capture
- Outcome Evidence
- Task engine
- override
- appointment status change

## Recommended next task

`Program 1 Phase B15 - Snapshot Capture Endpoint Prototype`

B15 smije izloziti service kroz uski backend endpoint samo ako ostane permission-gated, reason-required, audit-backed, preview-only i bez workflow side effecta.
