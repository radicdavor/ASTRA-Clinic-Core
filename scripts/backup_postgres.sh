#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-backups}"
POSTGRES_DB="${POSTGRES_DB:-astra_clinic}"
POSTGRES_USER="${POSTGRES_USER:-astra}"
CONTAINER="${POSTGRES_CONTAINER:-astra-clinic-core-db-1}"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"
docker exec "$CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$BACKUP_DIR/${POSTGRES_DB}_${STAMP}.dump"
echo "Backup created: $BACKUP_DIR/${POSTGRES_DB}_${STAMP}.dump"
