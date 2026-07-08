# Program 1 Phase D106 - Open Question Migration Rollback Notes

Status: documented

## Alembic Upgrade Path

The migration path adds `0019_clinical_open_questions` after `0018_clinical_findings`.

Expected upgrade:

```bash
alembic upgrade head
```

This creates the `clinical_open_questions` DB foundation table, constraints, FK references and indexes.

## Downgrade Path

The downgrade removes indexes and drops `clinical_open_questions`.

The downgrade must not mutate:

- patients
- clinical findings
- clinical documents
- appointments
- snapshots
- acknowledgments

## FK And Index Removal

Indexes are dropped before table removal. FK constraints are removed with the table.

## Source-Linking Implications

Dropping the table removes stored open question rows only. It must not rewrite source findings, source documents or extraction candidates.

## Demo And Test DB Implications

Demo/test databases may recreate the table through normal migration flow. Existing test data is disposable in local and CI contexts.

## Backup And Restore Future Needs

Production backup/restore rules are not approved. Before production use, maintainers must define retention, export, restore and legal review policy.

## Explicit No-Go Areas

- no production approval
- no real-data approval
- no endpoint approval
- no service approval
- no UI approval
- no automatic question creation approval
