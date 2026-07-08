# Program 1 Phase D29 - Findings Migration Rollback Notes

Status: migration rollback notes

## Upgrade Path

The D22-D32 migration adds `clinical_findings` through Alembic revision `0018_clinical_findings`.

Upgrade creates:

- the passive `clinical_findings` table
- patient, optional source document and optional reviewer foreign keys
- source-linking required text constraints
- safe lifecycle status constraint
- indexes for patient, lifecycle status, finding key, category, source type, source document and creation time

## Downgrade Path

Downgrade removes indexes first and then drops `clinical_findings`.

This is acceptable for demo/test environments because the phase does not approve real patient data or production use.

## Source-Linking Implications

Rollback removes stored finding rows. Source documents remain separate and are not changed by this migration.

## Demo Data and Test DB Implications

Seed data is not changed. Tests create findings directly through SQLAlchemy only to validate DB shape and constraints.

## Production Boundary

This migration is DB foundation only. It does not approve production use, real patient data, endpoint rollout, service writes or UI access.

## Future Backup/Restore Needs

Before production consideration, maintainers must define backup/restore validation for finding rows, source references, audit relationship and lifecycle metadata.

