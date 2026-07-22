from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

import psycopg

from recovery_common import (
    BACKUP_VERSION,
    DATABASE_DUMP_NAME,
    FILE_MANIFEST_NAME,
    MAIN_MANIFEST_NAME,
    STORAGE_DIRECTORY_NAME,
    RecoveryError,
    canonical_json_bytes,
    operation_log,
    require_database_url,
    resolved_child,
    run_postgres_tool,
    safe_relative_path,
    sha256_file,
    tool_version,
    utc_now,
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


def source_objects(connection: psycopg.Connection) -> list[SourceObject]:
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
    result: list[SourceObject] = []
    for document_id, relative_path, size, checksum, classification, content_type in rows:
        if not checksum or size is None:
            raise RecoveryError("source_object_metadata_incomplete")
        result.append(SourceObject(int(document_id), str(relative_path), int(size), str(checksum), str(classification), str(content_type)))
    return result


def git_commit() -> str:
    configured = os.environ.get("ASTRA_APPLICATION_COMMIT", "").strip()
    if configured:
        if not all(character in "0123456789abcdefABCDEF" for character in configured) or len(configured) < 7:
            raise RecoveryError("application_commit_invalid")
        return configured
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RecoveryError("application_commit_unavailable") from exc


def create_backup(args: argparse.Namespace) -> Path:
    database_url = require_database_url(args.database_url_env)
    output = args.output.resolve()
    storage_root = args.storage_root.resolve()
    operation_id = args.operation_id or uuid4().hex
    started = time.perf_counter()
    temporary = output.with_name(f".{output.name}.tmp-{operation_id}")
    operation_log(operation_id, "backup_started")
    if output.exists() and not args.overwrite:
        raise RecoveryError("backup_output_exists")
    if temporary.exists():
        raise RecoveryError("temporary_output_exists")
    if not storage_root.is_dir():
        raise RecoveryError("storage_root_missing")
    temporary.mkdir(parents=True)
    try:
        dump_path = temporary / DATABASE_DUMP_NAME
        run_postgres_tool(
            args.pg_dump,
            ["--format=custom", "--no-owner", "--no-privileges", f"--file={dump_path}"],
            database_url,
        )
        with psycopg.connect(database_url.replace("postgresql+psycopg://", "postgresql://", 1)) as connection:
            revision_row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            if not revision_row:
                raise RecoveryError("alembic_revision_missing")
            revision = str(revision_row[0])
            server_version = str(connection.info.server_version)
            objects = source_objects(connection)

        storage_output = temporary / STORAGE_DIRECTORY_NAME
        storage_output.mkdir()
        referenced: set[Path] = set()
        for item in objects:
            relative = safe_relative_path(item.relative_path)
            source = resolved_child(storage_root, relative)
            if not source.is_file():
                raise RecoveryError("source_object_missing")
            if source.stat().st_size != item.size or sha256_file(source) != item.sha256:
                raise RecoveryError("source_object_integrity_failed")
            referenced.add(relative)
            destination = resolved_child(storage_output, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        actual = {path.relative_to(storage_root) for path in storage_root.rglob("*") if path.is_file()}
        if actual != referenced:
            raise RecoveryError("unreferenced_or_missing_storage_objects")

        file_manifest = {"version": 1, "objects": [item.manifest_entry() for item in objects]}
        file_manifest_path = temporary / FILE_MANIFEST_NAME
        file_manifest_path.write_bytes(canonical_json_bytes(file_manifest))
        manifest = {
            "backup_version": BACKUP_VERSION,
            "created_at": utc_now(),
            "application_commit": git_commit(),
            "alembic_revision": revision,
            "postgres_server_version": server_version,
            "pg_dump_version": tool_version(args.pg_dump),
            "dump_sha256": sha256_file(dump_path),
            "file_storage_included": True,
            "file_manifest_sha256": sha256_file(file_manifest_path),
            "storage_object_count": len(objects),
        }
        write_json(temporary / MAIN_MANIFEST_NAME, manifest)
        if output.exists():
            if not args.overwrite:
                raise RecoveryError("backup_output_exists")
            shutil.rmtree(output)
        os.replace(temporary, output)
        operation_log(
            operation_id,
            "backup_completed",
            revision=revision,
            dump_sha256=manifest["dump_sha256"],
            file_manifest_sha256=manifest["file_manifest_sha256"],
            storage_object_count=len(objects),
            duration_ms=round((time.perf_counter() - started) * 1000),
        )
        return output
    except Exception as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        code = exc.code if isinstance(exc, RecoveryError) else "unexpected_backup_failure"
        operation_log(operation_id, "backup_failed", error_code=code, duration_ms=round((time.perf_counter() - started) * 1000))
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Create an atomic ASTRA PostgreSQL and document-storage backup")
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--storage-root", type=Path, required=True)
    result.add_argument("--database-url-env", default="DATABASE_URL")
    result.add_argument("--pg-dump", default="pg_dump")
    result.add_argument("--operation-id")
    result.add_argument("--overwrite", action="store_true")
    return result


def main() -> int:
    try:
        create_backup(parser().parse_args())
        return 0
    except RecoveryError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
