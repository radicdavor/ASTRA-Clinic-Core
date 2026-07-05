# Backup and Restore

Backups are mandatory before using ASTRA Clinic Core with real operational data.

## Local Backup

With Docker Compose running:

```bash
./scripts/backup_postgres.sh
```

The script writes a timestamped `pg_dump` custom-format file into `backups/`.

## Restore Example

```bash
docker compose exec -T db pg_restore \
  --clean \
  --if-exists \
  -U astra \
  -d astra_clinic \
  < backups/astra_clinic_YYYYMMDD_HHMMSS.dump
```

## Production Expectations

- Use encrypted backups.
- Store backups outside the primary database host.
- Test restore regularly.
- Define retention windows.
- Document who can access backups.
- Treat backups as sensitive patient and billing data.
