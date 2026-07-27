from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

import psycopg

from recovery_common import (
    DATABASE_DUMP_NAME,
    FILE_MANIFEST_NAME,
    MANIFEST_NAME,
    RECOVERY_SCHEMA_VERSION,
    STORAGE_DIRECTORY_NAME,
    SYNTHETIC_ENVIRONMENT,
    SYNTHETIC_MARKER,
    RecoveryError,
    canonical_json_bytes,
    database_identity,
    operation_log,
    psycopg_url,
    require_database_url,
    require_recovery_environment,
    public_tables,
    resolved_child,
    run_postgres_tool,
    safe_relative_path,
    semantic_snapshot,
    sha256_file,
    tool_version,
    utc_now,
    verified_private_copy,
    write_json,
)


@dataclass(frozen=True)
class SourceObject:
    document_id: int
    relative_path: str
    size: int
    sha256: str
    classification: str
    content_type: str

    def manifest_entry(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "relative_path": self.relative_path,
            "size": self.size,
            "sha256": self.sha256,
            "classification": self.classification,
            "content_type": self.content_type,
        }


def git_commit() -> str:
    configured = os.environ.get("ASTRA_APPLICATION_COMMIT", "").strip()
    if configured:
        if len(configured) != 40 or any(
            character not in "0123456789abcdefABCDEF" for character in configured
        ):
            raise RecoveryError("source_git_sha_invalid")
        return configured.lower()
    try:
        value = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RecoveryError("source_git_sha_unavailable") from exc
    if len(value) != 40:
        raise RecoveryError("source_git_sha_invalid")
    return value


def source_objects(connection: psycopg.Connection) -> list[SourceObject]:
    if "clinical_documents" not in public_tables(connection):
        return []
    rows = connection.execute(
        """
        SELECT id, attachment_path, file_size_bytes, checksum_sha256,
               COALESCE(record_classification, 'unclassified'),
               COALESCE(mime_type, 'application/octet-stream')
        FROM clinical_documents
        WHERE attachment_path IS NOT NULL
        ORDER BY id
        """
    ).fetchall()
    objects: list[SourceObject] = []
    for document_id, relative_path, size, checksum, classification, content_type in rows:
        if size is None or not checksum:
            raise RecoveryError("source_object_metadata_incomplete")
        objects.append(
            SourceObject(
                int(document_id),
                str(relative_path),
                int(size),
                str(checksum),
                str(classification),
                str(content_type),
            )
        )
    return objects


def _validate_output_path(output: Path) -> Path:
    if output.is_symlink() or output.exists():
        raise RecoveryError("backup_output_exists_or_unsafe")
    if output.parent.is_symlink():
        raise RecoveryError("backup_parent_unsafe")
    parent = output.parent.resolve()
    if not parent.is_dir():
        raise RecoveryError("backup_parent_unsafe")
    safe_relative_path(output.name)
    return parent / output.name


def create_backup(args: argparse.Namespace) -> Path | None:
    require_recovery_environment(args.environment_env)
    database_url = require_database_url(args.database_url_env)
    identity = database_identity(database_url)
    if args.storage_root.is_symlink():
        raise RecoveryError("storage_root_missing_or_unsafe")
    storage_root = args.storage_root.resolve()
    if not storage_root.is_dir():
        raise RecoveryError("storage_root_missing_or_unsafe")
    output = _validate_output_path(args.output)
    operation_id = args.operation_id or uuid4().hex
    operation_log(
        operation_id,
        "backup_preflight",
        environment=SYNTHETIC_ENVIRONMENT,
        target_host=identity["host"],
        target_database=identity["database"],
        dry_run=args.dry_run,
    )
    temporary = output.with_name(f".{output.name}.tmp-{operation_id}")
    if temporary.exists() or temporary.is_symlink():
        raise RecoveryError("temporary_output_exists_or_unsafe")
    if not args.dry_run:
        temporary.mkdir()
    try:
        with psycopg.connect(psycopg_url(database_url)) as connection:
            connection.execute(
                "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
            )
            recovery_marker = connection.execute(
                "SELECT to_regclass('public._astra_recovery_incomplete')"
            ).fetchone()[0]
            if recovery_marker is not None:
                raise RecoveryError("source_recovery_incomplete")
            snapshot = semantic_snapshot(connection)
            objects = source_objects(connection)
            postgres_version = str(connection.info.server_version)
            if args.dry_run:
                operation_log(
                    operation_id,
                    "backup_dry_run_completed",
                    revision=snapshot["revision"],
                    critical_tables=len(snapshot["critical_tables"]),
                    storage_object_count=len(objects),
                )
                return None
            exported_snapshot = str(
                connection.execute("SELECT pg_export_snapshot()").fetchone()[0]
            )
            dump_path = temporary / DATABASE_DUMP_NAME
            run_postgres_tool(
                args.pg_dump,
                [
                    "--format=custom",
                    "--no-owner",
                    "--no-privileges",
                    f"--snapshot={exported_snapshot}",
                    f"--file={dump_path}",
                ],
                database_url,
            )
        storage_output = temporary / STORAGE_DIRECTORY_NAME
        storage_output.mkdir()
        referenced: set[str] = set()
        for item in objects:
            relative = safe_relative_path(item.relative_path)
            source = resolved_child(storage_root, relative)
            if not source.is_file() or source.is_symlink():
                raise RecoveryError("source_object_missing_or_unsafe")
            if source.stat().st_size != item.size:
                raise RecoveryError("source_object_integrity_failed")
            referenced.add(relative.as_posix())
            destination = resolved_child(storage_output, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                verified_private_copy(source, destination, item.sha256)
            except RecoveryError as exc:
                raise RecoveryError("source_object_integrity_failed") from exc
            if destination.stat().st_size != item.size:
                raise RecoveryError("source_object_integrity_failed")

        actual = {
            path.relative_to(storage_root).as_posix()
            for path in storage_root.rglob("*")
            if path.is_file()
        }
        if actual != referenced:
            raise RecoveryError("unreferenced_or_missing_storage_objects")

        file_manifest = {
            "schema_version": 1,
            "objects": [item.manifest_entry() for item in objects],
        }
        file_manifest_path = temporary / FILE_MANIFEST_NAME
        file_manifest_path.write_bytes(canonical_json_bytes(file_manifest))
        dump_hash = sha256_file(dump_path)
        manifest = {
            "schema_version": RECOVERY_SCHEMA_VERSION,
            "source_git_sha": git_commit(),
            "source_environment": SYNTHETIC_ENVIRONMENT,
            "source_alembic_revision": snapshot["revision"],
            "postgresql_version": postgres_version,
            "created_at": utc_now(),
            "backup_filename": DATABASE_DUMP_NAME,
            "backup_size": dump_path.stat().st_size,
            "backup_sha256": dump_hash,
            "file_manifest_sha256": sha256_file(file_manifest_path),
            "semantic_snapshot": snapshot,
            "synthetic_marker": SYNTHETIC_MARKER,
            "forbidden_production": False,
            "tool_versions": {
                "pg_dump": tool_version(args.pg_dump),
                "python": sys.version.split()[0],
                "recovery_contract": RECOVERY_SCHEMA_VERSION,
            },
        }
        write_json(temporary / MANIFEST_NAME, manifest)
        os.replace(temporary, output)
        operation_log(
            operation_id,
            "backup_completed",
            revision=snapshot["revision"],
            backup_sha256=dump_hash,
            manifest_sha256=sha256_file(output / MANIFEST_NAME),
            critical_tables=len(snapshot["critical_tables"]),
            storage_object_count=len(objects),
        )
        return output
    except Exception as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        code = exc.code if isinstance(exc, RecoveryError) else "unexpected_backup_failure"
        operation_log(operation_id, "backup_failed", error_code=code)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Create an atomic synthetic ASTRA recovery backup"
    )
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--storage-root", type=Path, required=True)
    result.add_argument("--database-url-env", default="RECOVERY_SOURCE_DATABASE_URL")
    result.add_argument("--environment-env", default="ASTRA_RECOVERY_ENVIRONMENT")
    result.add_argument("--pg-dump", default="pg_dump")
    result.add_argument("--operation-id")
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    try:
        create_backup(parser().parse_args())
        return 0
    except RecoveryError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
