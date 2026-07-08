# Program 1 Phase D16 - Finding ORM Shape Deferral

Status: deferral

## Decision

Do not add `ClinicalFinding` ORM model in D16.

## Reason

This repository treats ORM persistence as a real runtime shape that should be paired with migration review. D0-D10 also added tests proving that `ClinicalFinding` model/table do not exist.

Adding an ORM draft now would weaken the no-migration/no-runtime boundary.

## Deferred Shape

Future model remains proposed only:

- `ClinicalFinding`
- `clinical_findings`
- patient/source references
- lifecycle status
- review metadata
- limitations
- schema version

## Still No-Go

- ORM model
- Alembic migration
- endpoint
- service
- UI
- permission seed

