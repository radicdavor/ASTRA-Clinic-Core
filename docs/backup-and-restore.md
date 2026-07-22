# Backup and restore runbook

This runbook covers the ASTRA PostgreSQL database and the canonical source
document directory as one recovery unit. The commands are validated only with
synthetic data. Production storage, encryption, retention and access policy
must be supplied by the deployment platform.

## Recovery image

Build the image from the same application commit being protected:

```bash
docker build -f backend/Dockerfile.recovery -t astra-recovery .
```

The image is pinned to PostgreSQL 16 client tools. Use a client major version
compatible with the server. `pg_dump` and `pg_restore` are the authoritative
database tools; the Python layer adds validation, storage reconciliation,
structured logging and safe failure behavior.

## Create a backup

Set `DATABASE_URL` in the process environment. Do not place credentials on the
command line or in a committed file.

```bash
python scripts/backup_postgres.py \
  --output /secure-backups/astra-2026-07-22 \
  --storage-root /app/data/documents
```

The output directory is published only after all checks pass. It contains:

- `database.dump`: custom-format PostgreSQL dump;
- `storage/`: exact opaque paths referenced by `ClinicalDocument` rows;
- `files.manifest.json`: document ID, relative path, size, SHA-256,
  classification and content type;
- `manifest.json`: format version, commit, Alembic revision, PostgreSQL/tool
  versions and checksums.

Patient names, OIBs, original filenames, database URLs and secrets are excluded
from manifests and operation logs. The command rejects missing, modified or
unreferenced storage objects and does not overwrite output unless `--overwrite`
is explicitly supplied.

## Restore to a new target

Stop application writes. Create a new empty database and an empty storage
location. Keep the old system unavailable until validation is complete.

```bash
export TARGET_DATABASE_URL='postgresql+psycopg://.../astra_recovered'
python scripts/restore_postgres.py \
  --artifact /secure-backups/astra-2026-07-22 \
  --target-storage /srv/astra-recovered/documents
```

Restore validates all manifests and checksums before changing the target. The
default rejects a non-empty database or storage directory. A
`_astra_recovery_incomplete` marker is created before `pg_restore`; `/ready`
returns not ready while it exists. Any failed restore must be remediated by
discarding the partial target and restarting with a new empty database and
storage location.

The restored database remains at the recorded revision by default. To restore a
known older backup and explicitly migrate it to the current single head:

```bash
python scripts/restore_postgres.py \
  --artifact /secure-backups/older \
  --target-storage /srv/astra-recovered/documents \
  --upgrade-head
```

No migration is hidden inside the normal restore path. After database and file
verification, active non-expired browser sessions are revoked before the marker
is removed.

## Verification checklist

1. Confirm manifest and dump/file hashes.
2. Confirm the restored Alembic revision and one migration head.
3. Run `python -m app.cli schema-status` against the target.
4. Confirm `/health` and `/ready`.
5. Create a new login; confirm a pre-disaster cookie is rejected.
6. Confirm clinic context, dashboard, clinical record, signed report/addendum,
   original source download, invoice and payment state.
7. Confirm cross-institution and unclassified-document denial.
8. Record the operation ID, artifact hash, duration and operator approval.

## Session retention maintenance

Normal cleanup is bounded and is not the post-restore revocation step:

```bash
python -m app.cli session-cleanup --dry-run --retention-days 30 --max-rows 10000
python -m app.cli session-cleanup --retention-days 30 --batch-size 500 --max-rows 5000
```

Example cron entry (deployment-specific environment loading is omitted):

```cron
17 3 * * * cd /srv/astra/backend && python -m app.cli session-cleanup --retention-days 30 --batch-size 500 --max-rows 5000
```

Windows Task Scheduler should invoke the same bounded command daily. Do not add
a permanent cleanup worker to the API process.

## Security boundary

The repository does not implement backup encryption. Production requires
platform-managed encryption at rest and in transit, restricted backup access,
separate key management, off-site copies, retention/deletion policy, access
audit and scheduled restore exercises. Environment secrets, TLS/DNS state and
provider credentials are backed up separately and never embedded in this
artifact.
