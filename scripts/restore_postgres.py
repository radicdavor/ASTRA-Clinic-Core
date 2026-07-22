from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
import psycopg

from recovery_common import (
    DATABASE_DUMP_NAME,
    FILE_MANIFEST_NAME,
    MAIN_MANIFEST_NAME,
    RECOVERY_MARKER_TABLE,
    STORAGE_DIRECTORY_NAME,
    RecoveryError,
    operation_log,
    postgres_environment,
    read_json,
    require_database_url,
    resolved_child,
    run_postgres_tool,
    safe_relative_path,
    sha256_file,
    validate_main_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def known_revisions() -> set[str]:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return {str(item.revision) for item in ScriptDirectory.from_config(config).walk_revisions()}


def require_known_revision(manifest: dict[str, object], revisions: set[str] | None = None) -> None:
    if manifest["alembic_revision"] not in (revisions if revisions is not None else known_revisions()):
        raise RecoveryError("unknown_backup_revision")


def validate_file_manifest(value: object) -> list[dict[str, object]]:
    if not isinstance(value, dict) or set(value) != {"version", "objects"} or value.get("version") != 1 or not isinstance(value.get("objects"), list):
        raise RecoveryError("invalid_file_manifest")
    allowed = {"document_id", "relative_path", "size", "sha256", "classification", "content_type"}
    entries: list[dict[str, object]] = []
    seen_ids: set[int] = set()
    seen_paths: set[str] = set()
    for raw in value["objects"]:
        if not isinstance(raw, dict) or set(raw) != allowed:
            raise RecoveryError("invalid_file_manifest_entry")
        if not isinstance(raw["document_id"], int) or not isinstance(raw["size"], int) or raw["size"] < 0:
            raise RecoveryError("invalid_file_manifest_entry")
        if not all(isinstance(raw[key], str) and raw[key] for key in ("relative_path", "sha256", "classification", "content_type")):
            raise RecoveryError("invalid_file_manifest_entry")
        safe_relative_path(str(raw["relative_path"]))
        if raw["document_id"] in seen_ids or raw["relative_path"] in seen_paths:
            raise RecoveryError("duplicate_file_manifest_entry")
        seen_ids.add(int(raw["document_id"]))
        seen_paths.add(str(raw["relative_path"]))
        entries.append(raw)
    return entries


def validate_artifact(artifact: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    manifest = validate_main_manifest(read_json(artifact / MAIN_MANIFEST_NAME))
    dump_path = artifact / DATABASE_DUMP_NAME
    file_manifest_path = artifact / FILE_MANIFEST_NAME
    if sha256_file(dump_path) != manifest["dump_sha256"] or sha256_file(file_manifest_path) != manifest["file_manifest_sha256"]:
        raise RecoveryError("backup_checksum_mismatch")
    entries = validate_file_manifest(read_json(file_manifest_path))
    if len(entries) != manifest["storage_object_count"]:
        raise RecoveryError("storage_object_count_mismatch")
    storage = artifact / STORAGE_DIRECTORY_NAME
    actual = {path.relative_to(storage).as_posix() for path in storage.rglob("*") if path.is_file()} if storage.is_dir() else set()
    expected = {str(entry["relative_path"]) for entry in entries}
    if actual != expected:
        raise RecoveryError("backup_storage_set_mismatch")
    for entry in entries:
        path = resolved_child(storage, safe_relative_path(str(entry["relative_path"])))
        if path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            raise RecoveryError("backup_storage_integrity_failed")
    return manifest, entries


def user_tables(connection: psycopg.Connection) -> set[str]:
    rows = connection.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()
    return {str(row[0]) for row in rows}


def create_marker(connection: psycopg.Connection, operation_id: str) -> None:
    connection.execute(f'CREATE TABLE "{RECOVERY_MARKER_TABLE}" (operation_id text NOT NULL, started_at timestamptz NOT NULL DEFAULT now())')
    connection.execute(f'INSERT INTO "{RECOVERY_MARKER_TABLE}" (operation_id) VALUES (%s)', (operation_id,))
    connection.commit()


def restore_storage(artifact: Path, target: Path, entries: list[dict[str, object]]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    source_root = artifact / STORAGE_DIRECTORY_NAME
    for entry in entries:
        relative = safe_relative_path(str(entry["relative_path"]))
        source = resolved_child(source_root, relative)
        destination = resolved_child(target, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def verify_restored(connection: psycopg.Connection, target_storage: Path, entries: list[dict[str, object]]) -> None:
    rows = connection.execute(
        """
        SELECT id, attachment_path, file_size_bytes, checksum_sha256,
               COALESCE(record_classification, 'unclassified'),
               COALESCE(mime_type, 'application/octet-stream')
        FROM clinical_documents WHERE attachment_path IS NOT NULL ORDER BY id
        """
    ).fetchall()
    expected = {
        int(item["document_id"]): (
            str(item["relative_path"]), int(item["size"]), str(item["sha256"]), str(item["classification"]), str(item["content_type"])
        )
        for item in entries
    }
    actual = {int(row[0]): (str(row[1]), int(row[2]), str(row[3]), str(row[4]), str(row[5])) for row in rows}
    if actual != expected:
        raise RecoveryError("restored_database_file_manifest_mismatch")
    for item in entries:
        path = resolved_child(target_storage, safe_relative_path(str(item["relative_path"])))
        if path.stat().st_size != item["size"] or sha256_file(path) != item["sha256"]:
            raise RecoveryError("restored_storage_integrity_failed")


def restore(args: argparse.Namespace) -> None:
    target_url = require_database_url(args.database_url_env)
    artifact = args.artifact.resolve()
    target_storage = args.target_storage.resolve()
    operation_id = args.operation_id or uuid4().hex
    started = time.perf_counter()
    marker_created = False
    operation_log(operation_id, "restore_started")
    try:
        manifest, entries = validate_artifact(artifact)
        require_known_revision(manifest)
        if target_storage.exists() and any(target_storage.iterdir()) and not args.allow_non_empty_storage:
            raise RecoveryError("target_storage_not_empty")
        normalized_url = target_url.replace("postgresql+psycopg://", "postgresql://", 1)
        with psycopg.connect(normalized_url) as connection:
            existing_tables = user_tables(connection)
            if existing_tables and not args.allow_non_empty_database:
                raise RecoveryError("target_database_not_empty")
            if RECOVERY_MARKER_TABLE in existing_tables:
                raise RecoveryError("target_recovery_already_incomplete")
            create_marker(connection, operation_id)
            marker_created = True

        run_postgres_tool(
            args.pg_restore,
            [
                "--exit-on-error",
                "--no-owner",
                "--no-privileges",
                f"--dbname={postgres_environment(target_url)['PGDATABASE']}",
                str(artifact / DATABASE_DUMP_NAME),
            ],
            target_url,
        )
        if args.upgrade_head:
            environment = os.environ.copy()
            environment["DATABASE_URL"] = target_url
            try:
                subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=environment, check=True)
            except subprocess.CalledProcessError as exc:
                raise RecoveryError("explicit_alembic_upgrade_failed") from exc

        restore_storage(artifact, target_storage, entries)
        with psycopg.connect(normalized_url) as connection:
            revision_row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            if not revision_row or str(revision_row[0]) not in known_revisions():
                raise RecoveryError("restored_revision_unknown")
            if not args.upgrade_head and str(revision_row[0]) != manifest["alembic_revision"]:
                raise RecoveryError("restored_revision_mismatch")
            verify_restored(connection, target_storage, entries)
            revoked = connection.execute(
                "UPDATE user_sessions SET revoked_at=now() WHERE revoked_at IS NULL AND expires_at > now()"
            ).rowcount
            connection.execute(f'DROP TABLE "{RECOVERY_MARKER_TABLE}"')
            connection.commit()
        operation_log(
            operation_id,
            "restore_completed",
            revision=str(revision_row[0]),
            revoked_sessions=int(revoked or 0),
            storage_object_count=len(entries),
            duration_ms=round((time.perf_counter() - started) * 1000),
        )
    except Exception as exc:
        code = exc.code if isinstance(exc, RecoveryError) else "unexpected_restore_failure"
        operation_log(operation_id, "restore_failed", error_code=code, recovery_marker_present=marker_created, duration_ms=round((time.perf_counter() - started) * 1000))
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Restore and verify an ASTRA backup into a new target")
    result.add_argument("--artifact", type=Path, required=True)
    result.add_argument("--target-storage", type=Path, required=True)
    result.add_argument("--database-url-env", default="TARGET_DATABASE_URL")
    result.add_argument("--pg-restore", default="pg_restore")
    result.add_argument("--operation-id")
    result.add_argument("--allow-non-empty-database", action="store_true")
    result.add_argument("--allow-non-empty-storage", action="store_true")
    result.add_argument("--upgrade-head", action="store_true", help="Explicitly run Alembic upgrade head after restoring an older known revision")
    return result


def main() -> int:
    try:
        restore(parser().parse_args())
        return 0
    except RecoveryError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
