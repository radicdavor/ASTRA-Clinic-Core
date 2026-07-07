# Program 1 Phase B19 - Regression Notes

Status: snapshot detail read-only view

## Implemented

B19 dodaje read-only detail view za spremljeni Clinical Readiness Snapshot.

Implementirano:

- backend snapshot detail response schema
- backend appointment-scoped snapshot detail endpoint
- frontend snapshot detail type
- frontend snapshot detail API client
- read-only detail panel u Appointment Workspaceu
- prikaz copied snapshot payloada:
  - items
  - limitations
  - source warnings
  - source refs
  - template metadata
  - reason
  - disclaimer
- regression coverage za auth, permission, appointment scope, full payload i read-only side effects
- frontend smoke coverage za detail panel i zabranjene kontrole

## Behavioral changes

Korisnik sada iz Appointment Workspace snapshot historyja moze otvoriti read-only detalje spremljenog snapshota.

Detail prikaz ne mijenja podatke i ne pise audit by default.

## API compatibility

Novi read-only endpoint:

`GET /api/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}`

Endpoint zahtijeva:

- authenticated user
- permission `clinical_readiness.snapshots.read`
- snapshot mora pripadati appointmentu iz rute

Postojeci capture i history endpointi ostaju nepromijenjeni.

## Safety properties

B19 cuva sljedece granice:

- detail endpoint je read-only
- detail endpoint ne pise audit by default
- detail endpoint ne stvara snapshot
- detail endpoint ne mijenja appointment status
- detail endpoint ne stvara Task
- detail endpoint ne stvara Outcome Evidence
- detail endpoint ne stvara ClinicalPlan
- detail endpoint ne stvara ClinicalEpisode
- frontend detail panel nema edit/delete/supersession kontrole
- frontend detail panel ne prikazuje snapshot kao odobrenje, clearance, task ili workflow odluku

## Not implemented

B19 nije implementirao:

- snapshot edit
- snapshot delete
- snapshot supersession
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production governance
- real AI/OCR
- real patient data

## Remaining risks

- nema supersession UX-a
- nema DB-level immutable update prevention izvan postojece discipline modela/ruta
- idempotency persistence ostaje deferred
- permission UX ostaje osnovan
- production governance nije kompletan
- backend test environment mora ostati stabilan prije sire uporabe

## Go / No-Go

Go za sljedeci safety korak:

`Program 1 Phase B20 - Snapshot Idempotency and Duplicate-Capture Guard`

Razlog:

Prije supersessiona ili sire production-like uporabe treba rijesiti duplicate capture protection jer request schema vec prima `idempotency_key`.

No-Go za:

- supersession prije idempotency guardraila
- edit/delete snapshot
- approval/clearance wording
- Task engine
- Outcome Evidence
- appointment status change

## Recommended next task

`Program 1 Phase B20 - Snapshot Idempotency and Duplicate-Capture Guard`
