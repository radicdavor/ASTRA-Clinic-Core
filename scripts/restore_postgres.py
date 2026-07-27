from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

from alembic.config import Config
from alembic.script import ScriptDirectory
import psycopg

from recovery_common import (
    DATABASE_DUMP_NAME,
    FILE_MANIFEST_NAME,
    FINAL_ALEMBIC_REVISION,
    MANIFEST_NAME,
    RECOVERY_MARKER_TABLE,
    STORAGE_DIRECTORY_NAME,
    SUPPORTED_BACKUP_REVISIONS,
    SYNTHETIC_ENVIRONMENT,
    RecoveryError,
    database_identity,
    operation_log,
    postgres_environment,
    psycopg_url,
    public_tables,
    read_alembic_revision,
    read_json,
    require_database_url,
    require_recovery_environment,
    require_safe_artifact_root,
    resolved_child,
    run_postgres_tool,
    safe_relative_path,
    semantic_snapshot,
    sha256_file,
    validate_main_manifest,
    verified_private_copy,
)


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
DESTRUCTIVE_CONFIRMATION = "RESTORE_SYNTHETIC_DISPOSABLE_DATABASE"


def known_revisions() -> set[str]:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return {
        str(item.revision)
        for item in ScriptDirectory.from_config(config).walk_revisions()
    }


def validate_file_manifest(value: object) -> list[dict[str, object]]:
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "objects"}
        or value.get("schema_version") != 1
        or not isinstance(value.get("objects"), list)
    ):
        raise RecoveryError("invalid_file_manifest")
    required = {
        "document_id",
        "relative_path",
        "size",
        "sha256",
        "classification",
        "content_type",
    }
    entries: list[dict[str, object]] = []
    seen_ids: set[int] = set()
    seen_paths: set[str] = set()
    for raw in value["objects"]:
        if not isinstance(raw, dict) or set(raw) != required:
            raise RecoveryError("invalid_file_manifest_entry")
        if (
            not isinstance(raw["document_id"], int)
            or not isinstance(raw["size"], int)
            or raw["size"] < 0
            or not isinstance(raw["sha256"], str)
            or len(raw["sha256"]) != 64
        ):
            raise RecoveryError("invalid_file_manifest_entry")
        if not all(
            isinstance(raw[key], str) and raw[key]
            for key in ("relative_path", "classification", "content_type")
        ):
            raise RecoveryError("invalid_file_manifest_entry")
        safe_relative_path(str(raw["relative_path"]))
        if raw["document_id"] in seen_ids or raw["relative_path"] in seen_paths:
            raise RecoveryError("duplicate_file_manifest_entry")
        seen_ids.add(int(raw["document_id"]))
        seen_paths.add(str(raw["relative_path"]))
        entries.append(raw)
    return entries


def validate_artifact(
    artifact: Path,
) -> tuple[dict[str, object], list[dict[str, object]], str]:
    artifact = require_safe_artifact_root(artifact, must_exist=True)
    manifest_path = resolved_child(artifact, safe_relative_path(MANIFEST_NAME))
    manifest = validate_main_manifest(read_json(manifest_path))
    if manifest["source_alembic_revision"] not in known_revisions():
        raise RecoveryError("unknown_backup_revision")
    dump_path = resolved_child(artifact, safe_relative_path(DATABASE_DUMP_NAME))
    file_manifest_path = resolved_child(
        artifact, safe_relative_path(FILE_MANIFEST_NAME)
    )
    if dump_path.stat().st_size != manifest["backup_size"]:
        raise RecoveryError("backup_size_mismatch")
    if sha256_file(dump_path) != manifest["backup_sha256"]:
        raise RecoveryError("backup_checksum_mismatch")
    if sha256_file(file_manifest_path) != manifest["file_manifest_sha256"]:
        raise RecoveryError("file_manifest_checksum_mismatch")
    entries = validate_file_manifest(read_json(file_manifest_path))
    storage_root = resolved_child(artifact, safe_relative_path(STORAGE_DIRECTORY_NAME))
    if not storage_root.is_dir() or storage_root.is_symlink():
        raise RecoveryError("backup_storage_missing_or_unsafe")
    actual = {
        path.relative_to(storage_root).as_posix()
        for path in storage_root.rglob("*")
        if path.is_file()
    }
    expected = {str(entry["relative_path"]) for entry in entries}
    if actual != expected:
        raise RecoveryError("backup_storage_set_mismatch")
    for entry in entries:
        path = resolved_child(
            storage_root, safe_relative_path(str(entry["relative_path"]))
        )
        if (
            path.is_symlink()
            or path.stat().st_size != entry["size"]
            or sha256_file(path) != entry["sha256"]
        ):
            raise RecoveryError("backup_storage_integrity_failed")
    return manifest, entries, sha256_file(manifest_path)


def _target_is_empty(connection: psycopg.Connection) -> bool:
    rows = connection.execute(
        """
        SELECT tablename FROM pg_tables
        WHERE schemaname='public'
        """
    ).fetchall()
    return not rows


def _create_marker(connection: psycopg.Connection, operation_id: str) -> None:
    connection.execute(
        f"""
        CREATE TABLE "{RECOVERY_MARKER_TABLE}" (
            operation_id text NOT NULL,
            started_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    connection.execute(
        f'INSERT INTO "{RECOVERY_MARKER_TABLE}" (operation_id) VALUES (%s)',
        (operation_id,),
    )
    connection.commit()


def _run_alembic_upgrade(database_url: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", FINAL_ALEMBIC_REVISION],
            cwd=BACKEND,
            env=environment,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RecoveryError("post_restore_alembic_upgrade_failed") from exc


def _restore_storage(
    artifact: Path,
    target: Path,
    entries: list[dict[str, object]],
    operation_id: str,
) -> Path:
    if target.is_symlink() or (
        target.exists() and (not target.is_dir() or any(target.iterdir()))
    ):
        raise RecoveryError("target_storage_not_empty_or_unsafe")
    if target.parent.is_symlink():
        raise RecoveryError("target_storage_parent_unsafe")
    parent = target.parent.resolve()
    if not parent.is_dir():
        raise RecoveryError("target_storage_parent_unsafe")
    staging = target.with_name(f".{target.name}.restore-{operation_id}")
    if staging.exists() or staging.is_symlink():
        raise RecoveryError("target_storage_staging_exists")
    staging.mkdir()
    source_root = resolved_child(artifact, safe_relative_path(STORAGE_DIRECTORY_NAME))
    try:
        for entry in entries:
            relative = safe_relative_path(str(entry["relative_path"]))
            source = resolved_child(source_root, relative)
            destination = resolved_child(staging, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            verified_private_copy(source, destination, str(entry["sha256"]))
            if (
                destination.stat().st_size != entry["size"]
            ):
                raise RecoveryError("restored_storage_integrity_failed")
        if target.exists():
            target.rmdir()
        os.replace(staging, target)
        return target
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _verify_database_files(
    connection: psycopg.Connection,
    target_storage: Path,
    entries: list[dict[str, object]],
    *,
    enforce_source_classification: bool,
) -> None:
    if "clinical_documents" not in set(public_tables(connection)):
        if entries:
            raise RecoveryError("restored_database_file_manifest_mismatch")
        return
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
    expected = {
        int(item["document_id"]): (
            str(item["relative_path"]),
            int(item["size"]),
            str(item["sha256"]),
            str(item["content_type"]),
            *(
                (str(item["classification"]),)
                if enforce_source_classification
                else ()
            ),
        )
        for item in entries
    }
    actual = {
        int(row[0]): (
            str(row[1]),
            int(row[2]),
            str(row[3]),
            str(row[5]),
            *((str(row[4]),) if enforce_source_classification else ()),
        )
        for row in rows
    }
    if actual != expected:
        raise RecoveryError("restored_database_file_manifest_mismatch")
    for entry in entries:
        path = resolved_child(
            target_storage, safe_relative_path(str(entry["relative_path"]))
        )
        if (
            path.stat().st_size != entry["size"]
            or sha256_file(path) != entry["sha256"]
        ):
            raise RecoveryError("restored_storage_integrity_failed")


def _assert_snapshot_equal(
    expected: dict[str, object], actual: dict[str, object]
) -> None:
    if actual != expected:
        raise RecoveryError("restored_semantic_snapshot_mismatch")


def _assert_final_invariants(snapshot: dict[str, object]) -> None:
    if snapshot["revision"] != FINAL_ALEMBIC_REVISION:
        raise RecoveryError("final_revision_mismatch")
    invariants = snapshot["invariants"]
    if invariants.get("alembic_revision_rows") != 1:
        raise RecoveryError("alembic_revision_row_count_invalid")
    for key in (
        "unvalidated_foreign_keys",
        "duplicate_clinic_memberships",
        "orphaned_document_institutions",
    ):
        if invariants.get(key, 0) != 0:
            raise RecoveryError(f"final_invariant_failed_{key}")


def restore(args: argparse.Namespace) -> dict[str, object]:
    require_recovery_environment(args.environment_env)
    target_url = require_database_url(args.database_url_env)
    identity = database_identity(target_url)
    artifact = require_safe_artifact_root(args.artifact, must_exist=True)
    operation_id = args.operation_id or uuid4().hex
    manifest, entries, manifest_hash = validate_artifact(artifact)
    if args.expected_manifest_sha256 != manifest_hash:
        raise RecoveryError("expected_manifest_checksum_mismatch")
    source_revision = str(manifest["source_alembic_revision"])
    if args.expected_source_revision != source_revision:
        raise RecoveryError("expected_source_revision_mismatch")
    needs_upgrade = source_revision != FINAL_ALEMBIC_REVISION
    if needs_upgrade and not args.upgrade_head:
        raise RecoveryError("older_backup_requires_roll_forward")
    if args.dry_run:
        operation_log(
            operation_id,
            "restore_dry_run_completed",
            environment=SYNTHETIC_ENVIRONMENT,
            target_host=identity["host"],
            target_database=identity["database"],
            source_revision=source_revision,
            final_revision=FINAL_ALEMBIC_REVISION,
            manifest_sha256=manifest_hash,
        )
        return {
            "source_revision": source_revision,
            "restored_revision": None,
            "final_revision": None,
            "backup_sha256": manifest["backup_sha256"],
            "manifest_sha256": manifest_hash,
            "dry_run": True,
        }
    if args.confirm_destructive != DESTRUCTIVE_CONFIRMATION:
        raise RecoveryError("destructive_confirmation_required")

    target_storage = args.target_storage.absolute()
    operation_log(
        operation_id,
        "restore_started",
        environment=SYNTHETIC_ENVIRONMENT,
        target_host=identity["host"],
        target_database=identity["database"],
        source_revision=source_revision,
        roll_forward=needs_upgrade,
    )
    marker_created = False
    try:
        with psycopg.connect(psycopg_url(target_url)) as connection:
            if not _target_is_empty(connection):
                raise RecoveryError("target_database_not_empty")
            _create_marker(connection, operation_id)
            marker_created = True

        with TemporaryDirectory(prefix="astra-verified-restore-") as temporary:
            verified_dump = Path(temporary) / DATABASE_DUMP_NAME
            verified_private_copy(
                resolved_child(artifact, safe_relative_path(DATABASE_DUMP_NAME)),
                verified_dump,
                str(manifest["backup_sha256"]),
            )
            run_postgres_tool(
                args.pg_restore,
                [
                    "--exit-on-error",
                    "--no-owner",
                    "--no-privileges",
                    f"--dbname={postgres_environment(target_url)['PGDATABASE']}",
                    str(verified_dump),
                ],
                target_url,
            )

        with psycopg.connect(psycopg_url(target_url)) as connection:
            restored_revision = read_alembic_revision(connection)
            if restored_revision != source_revision:
                raise RecoveryError("restored_revision_mismatch")
            restored_snapshot = semantic_snapshot(connection)
            _assert_snapshot_equal(
                manifest["semantic_snapshot"],
                restored_snapshot,
            )

        if needs_upgrade:
            _run_alembic_upgrade(target_url)

        restored_storage = _restore_storage(
            artifact, target_storage, entries, operation_id
        )
        with psycopg.connect(psycopg_url(target_url)) as connection:
            final_revision = read_alembic_revision(connection)
            final_snapshot = semantic_snapshot(connection)
            _assert_final_invariants(final_snapshot)
            _verify_database_files(
                connection,
                restored_storage,
                entries,
                enforce_source_classification=(
                    source_revision == FINAL_ALEMBIC_REVISION
                ),
            )
            active_sessions_revoked = 0
            if "user_sessions" in set(public_tables(connection)):
                active_sessions_revoked = int(
                    connection.execute(
                        """
                        UPDATE user_sessions SET revoked_at=now()
                        WHERE revoked_at IS NULL AND expires_at > now()
                        """
                    ).rowcount
                    or 0
                )
            connection.execute(f'DROP TABLE "{RECOVERY_MARKER_TABLE}"')
            connection.commit()
        operation_log(
            operation_id,
            "restore_completed",
            restored_revision=restored_revision,
            final_revision=final_revision,
            backup_sha256=manifest["backup_sha256"],
            manifest_sha256=manifest_hash,
            active_sessions_revoked=active_sessions_revoked,
            cleanup_status="marker_removed",
        )
        return {
            "source_revision": source_revision,
            "restored_revision": restored_revision,
            "final_revision": final_revision,
            "backup_sha256": manifest["backup_sha256"],
            "manifest_sha256": manifest_hash,
            "dry_run": False,
            "active_sessions_revoked": active_sessions_revoked,
        }
    except Exception as exc:
        code = exc.code if isinstance(exc, RecoveryError) else "unexpected_restore_failure"
        operation_log(
            operation_id,
            "restore_failed",
            error_code=code,
            recovery_marker_present=marker_created,
        )
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Fail-closed ASTRA restore for synthetic disposable databases"
    )
    result.add_argument("--artifact", type=Path, required=True)
    result.add_argument("--target-storage", type=Path, required=True)
    result.add_argument("--expected-source-revision", required=True)
    result.add_argument("--expected-manifest-sha256", required=True)
    result.add_argument("--database-url-env", default="RECOVERY_TARGET_DATABASE_URL")
    result.add_argument("--environment-env", default="ASTRA_RECOVERY_ENVIRONMENT")
    result.add_argument("--pg-restore", default="pg_restore")
    result.add_argument("--operation-id")
    result.add_argument("--upgrade-head", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--confirm-destructive")
    return result


def main() -> int:
    try:
        restore(parser().parse_args())
        return 0
    except RecoveryError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
