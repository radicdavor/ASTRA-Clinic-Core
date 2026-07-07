# Program 1 Phase B13 - Regression Notes

Status: migration/model-only persistence draft

## Implemented

B13 dodaje najuzi persistence foundation za buduci Clinical Readiness Snapshot.

Implementirano:

- SQLAlchemy model `ClinicalReadinessSnapshot`
- Alembic migracija za `clinical_readiness_snapshots`
- persistence-shape regression coverage

Model i migracija spremaju immutable-looking copied preview payload:

- appointment reference
- patient reference
- service reference
- actor reference
- schema version
- preview generated timestamp
- preview status and summary
- template metadata
- reason
- preview-only marker
- JSON payload fields
- disclaimer
- future supersession metadata

## Behavioral changes

Runtime aplikacije ne mijenja ponasanje.

Jedina promjena nakon migracije je postojanje nove DB tablice.

Nema novog API endpointa.

Nema UI promjene.

## API compatibility

Nema API path promjena.

Postojeci preview endpoint ostaje:

`GET /api/appointments/{appointment_id}/clinical-readiness-preview`

Preview ostaje read-only i ne sprema snapshot.

## Not implemented

B13 nije implementirao:

- capture endpoint
- capture service
- permission enforcement
- audit write
- snapshot history UI
- capture button
- supersession UI
- Outcome Evidence
- Task engine
- override
- appointment status change
- patient messaging
- real AI/OCR
- real patient data
- production/certification claim

## Safety properties

B13 cuva sljedece granice:

- snapshot tablica ne znaci clinical approval
- snapshot tablica ne znaci readiness override
- snapshot tablica ne stvara Task
- snapshot tablica ne stvara Outcome Evidence
- snapshot tablica ne stvara ClinicalPlan
- snapshot tablica ne stvara ClinicalEpisode
- snapshot tablica ne mijenja appointment status
- preview GET ne persistira snapshot
- Patient Clinical Summary ne postaje source of truth
- unreviewed AI ne postaje official knowledge

## Remaining risks

- snapshot table exists but is not used by runtime
- no capture transaction yet
- no permission enforcement yet
- no audit event yet
- no history UI
- no supersession behavior yet
- production governance is not complete

## Go / No-Go

Go za sljedeci uski backend service korak:

`Program 1 Phase B14 - Snapshot Capture Service Prototype`

No-Go za:

- capture endpoint
- frontend capture button
- snapshot history UI
- permission bypass
- audit-free capture
- Outcome Evidence
- Task engine
- override
- appointment status change

## Recommended next task

`Program 1 Phase B14 - Snapshot Capture Service Prototype`

B14 mora i dalje izbjeci endpoint i UI. Treba implementirati server-side capture service koji rebuilda preview, sprema copied payload i priprema atomic audit behavior bez javne rute.
