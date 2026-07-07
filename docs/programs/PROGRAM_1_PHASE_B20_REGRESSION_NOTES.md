# Program 1 Phase B20 - Regression Notes

Status: snapshot idempotency and duplicate-capture guard

## Implemented

B20 uvodi stvarnu idempotency podrsku za Clinical Readiness Snapshot capture.

Implementirano:

- nullable persistence columns:
  - `idempotency_key`
  - `idempotency_fingerprint`
- composite unique constraint za appointment/user/key
- Alembic migration `0015_snapshot_idempotency.py`
- idempotency guard u capture serviceu
- conflict behavior za isti key s drugim fingerprintom
- frontend idempotency key generation
- frontend retry koristi isti key dok je modal otvoren
- frontend resetira key nakon uspjeha ili odustajanja
- regression coverage za duplicate-capture guard

## Behavioral changes

Ako capture nema `idempotency_key`, ponasanje ostaje isto: svaki eksplicitni capture moze stvoriti novi snapshot.

Ako capture ima `idempotency_key`:

- isti appointment, isti user, isti key i isti fingerprint vracaju postojeci snapshot
- drugi audit event se ne pise
- novi snapshot se ne stvara
- isti key s drugim reasonom vraca conflict

Fingerprint se racuna iz:

- appointment id
- actor user id
- cleaned reason
- schema version

Client preview payload nije dio fingerprinta.

## API compatibility

Postojeci endpoint ostaje:

`POST /api/appointments/{appointment_id}/clinical-readiness-snapshots`

Request schema je vec podrzavala `idempotency_key`; B20 uskladjuje runtime ponasanje s tim contractom.

Conflict za isti key s drugim fingerprintom vraca `409 Conflict`.

## Safety properties

B20 cuva sljedece granice:

- capture ostaje reason-required
- capture ostaje permission-gated
- capture ostaje audit-backed
- capture ostaje preview-only
- capture ne vjeruje client preview payloadu
- capture rebuilda server-side preview za novi capture
- duplicate retry ne pise drugi audit event
- capture ne mijenja appointment status
- capture ne stvara Task
- capture ne stvara Outcome Evidence
- capture ne stvara ClinicalPlan
- capture ne stvara ClinicalEpisode

## Not implemented

B20 nije implementirao:

- supersession
- edit/delete
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- production governance

## Remaining risks

- idempotency fingerprint je namjerno uzak i ne ukljucuje preview payload
- idempotency conflict UX je osnovan
- supersession UX jos ne postoji
- canonical disclaimer hardening jos nije zavrsen
- DB-level immutability guard izvan ruta jos nije implementiran

## Recommended next task

`Program 1 Phase B21 - Snapshot Canonical Disclaimer and Immutability Hardening`
