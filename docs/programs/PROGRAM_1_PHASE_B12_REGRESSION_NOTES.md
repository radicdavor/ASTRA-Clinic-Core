# Program 1 Phase B12 - Regression Notes

Status: documentation-only permission and audit contract pass

## Implemented

B12 definira permission i audit contract za buduci Clinical Readiness Snapshot capture.

Implementirano dokumentacijski:

- snapshot permission contract
- snapshot audit payload contract
- permission/audit no-go matrix
- snapshot implementation gate

Novi dokumenti:

- `PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_CONTRACT.md`
- `PROGRAM_1_PHASE_B12_SNAPSHOT_AUDIT_PAYLOAD_CONTRACT.md`
- `PROGRAM_1_PHASE_B12_SNAPSHOT_PERMISSION_AUDIT_NO_GO_MATRIX.md`
- `PROGRAM_1_PHASE_B12_SNAPSHOT_IMPLEMENTATION_GATE.md`

## Behavioral changes

Nema behavioral changes.

B12 ne mijenja backend, frontend, API response, bazu, migracije, RBAC seed, audit runtime ili UI.

## Not implemented

B12 nije implementirao:

- permissions u kodu
- RBAC seed promjene
- audit events u kodu
- DB snapshot model
- Alembic migraciju
- capture endpoint
- frontend capture UI
- snapshot history UI
- permission enforcement
- Outcome Evidence
- Task engine
- override
- appointment status promjenu
- real AI/OCR
- real patient data

## Remaining risks

- permission model jos nije implementiran
- audit event jos nije implementiran
- snapshot persistence jos nije implementiran
- capture endpoint jos ne postoji
- snapshot history UI jos ne postoji
- supersession behavior jos nije implementiran
- production governance jos nije odobren
- buduca implementacija mora paziti da snapshot ne izgleda kao clinical approval

## B12 decision

Buduci Clinical Readiness Snapshot capture mora biti:

- permission-gated
- explicit user action
- reason-required
- auditiran
- atomican sa snapshot saveom
- preview-only
- immutable
- source-linked
- bez unreviewed AI kao official source
- bez Patient Clinical Summary kao source truth
- bez appointment status promjene
- bez taskova
- bez Outcome Evidencea
- bez overridea

Default mora biti deny.

AI agent, system job i API key nemaju snapshot capture pravo by default.

## Go / No-Go

Go za sljedeci uski architecture/code-prep korak:

`Program 1 Phase B13 - Snapshot Persistence Migration Draft`

No-Go za:

- capture endpoint bez permission enforcementa
- capture bez reasona
- capture bez audit eventa
- frontend capture button prije reason UI-ja
- Outcome Evidence
- Task engine
- override
- appointment status change
- production/certification claim

## Recommended next task

`Program 1 Phase B13 - Snapshot Persistence Migration Draft`

Razlog:

Sljedeci najuzni sigurni korak je migration-only draft za immutable snapshot tablicu. Endpoint, UI i audit runtime trebaju ostati izvan B13 ako maintainer ne odobri siri scope.
