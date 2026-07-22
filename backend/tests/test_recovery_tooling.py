from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from recovery_common import (  # noqa: E402
    RecoveryError,
    operation_log,
    postgres_environment,
    safe_relative_path,
    validate_main_manifest,
    write_json,
    sha256_file,
)
from restore_postgres import require_known_revision, validate_artifact, validate_file_manifest  # noqa: E402
from backup_postgres import git_commit  # noqa: E402


def valid_manifest() -> dict[str, object]:
    return {
        "backup_version": 1,
        "created_at": "2026-07-22T00:00:00+00:00",
        "application_commit": "a" * 40,
        "alembic_revision": "0062_signed_report_addendum_integrity",
        "postgres_server_version": "160014",
        "pg_dump_version": "pg_dump (PostgreSQL) 16.14",
        "dump_sha256": "b" * 64,
        "file_storage_included": True,
        "file_manifest_sha256": "c" * 64,
        "storage_object_count": 0,
    }


def test_manifest_rejects_secret_or_unknown_fields():
    manifest = valid_manifest()
    manifest["database_url"] = "postgresql://should-not-appear"

    with pytest.raises(RecoveryError, match="unsupported_backup_manifest"):
        validate_main_manifest(manifest)


@pytest.mark.parametrize("path", ["../escape.pdf", "/absolute.pdf", "folder/../../escape", "folder/name with space.pdf"])
def test_storage_path_rejects_escape_and_uncontrolled_names(path: str):
    with pytest.raises(RecoveryError, match="unsafe_storage_path"):
        safe_relative_path(path)


def test_postgres_environment_keeps_credentials_out_of_command_data(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    environment = postgres_environment("postgresql+psycopg://user:password@db:5433/astra_restore?sslmode=require")

    assert environment["PGHOST"] == "db"
    assert environment["PGPORT"] == "5433"
    assert environment["PGDATABASE"] == "astra_restore"
    assert environment["PGPASSWORD"] == "password"
    assert "DATABASE_URL" not in environment


def test_file_manifest_rejects_duplicates_and_unknown_fields():
    entry = {
        "document_id": 1,
        "relative_path": "1/opaque.pdf",
        "size": 4,
        "sha256": "a" * 64,
        "classification": "clinical",
        "content_type": "application/pdf",
    }
    with pytest.raises(RecoveryError, match="duplicate_file_manifest_entry"):
        validate_file_manifest({"version": 1, "objects": [entry, dict(entry)]})
    with pytest.raises(RecoveryError, match="invalid_file_manifest_entry"):
        validate_file_manifest({"version": 1, "objects": [{**entry, "original_filename": "patient-name.pdf"}]})


def test_structured_logging_redacts_credentials_and_content(capsys):
    operation_log(
        "operation-1",
        "restore_failed",
        database_url="postgresql://user:secret@db/astra",
        session_token="raw-token",
        patient_name="Synthetic Person",
        error_code="checksum_mismatch",
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["database_url"] == "[REDACTED]"
    assert payload["session_token"] == "[REDACTED]"
    assert payload["patient_name"] == "[REDACTED]"
    assert payload["error_code"] == "checksum_mismatch"
    assert "secret" not in json.dumps(payload)


def test_application_commit_accepts_explicit_container_value(monkeypatch):
    monkeypatch.setenv("ASTRA_APPLICATION_COMMIT", "159de86")
    assert git_commit() == "159de86"


def test_application_commit_rejects_non_hash_value(monkeypatch):
    monkeypatch.setenv("ASTRA_APPLICATION_COMMIT", "not-a-commit")
    with pytest.raises(RecoveryError, match="application_commit_invalid"):
        git_commit()


def artifact(tmp_path: Path) -> Path:
    root = tmp_path / "backup"
    storage = root / "storage"
    storage.mkdir(parents=True)
    dump = root / "database.dump"
    dump.write_bytes(b"synthetic-dump")
    source = storage / "1" / "opaque.bin"
    source.parent.mkdir()
    source.write_bytes(b"synthetic-object")
    file_manifest = {
        "version": 1,
        "objects": [
            {
                "document_id": 1,
                "relative_path": "1/opaque.bin",
                "size": source.stat().st_size,
                "sha256": sha256_file(source),
                "classification": "clinical",
                "content_type": "application/octet-stream",
            }
        ],
    }
    write_json(root / "files.manifest.json", file_manifest)
    manifest = valid_manifest()
    manifest.update(
        {
            "dump_sha256": sha256_file(dump),
            "file_manifest_sha256": sha256_file(root / "files.manifest.json"),
            "storage_object_count": 1,
        }
    )
    write_json(root / "manifest.json", manifest)
    return root


def test_artifact_rejects_corrupt_dump(tmp_path):
    root = artifact(tmp_path)
    (root / "database.dump").write_bytes(b"corrupt")
    with pytest.raises(RecoveryError, match="backup_checksum_mismatch"):
        validate_artifact(root)


@pytest.mark.parametrize("mode", ["missing", "extra", "corrupt"])
def test_artifact_rejects_storage_mismatch(tmp_path, mode: str):
    root = artifact(tmp_path)
    source = root / "storage" / "1" / "opaque.bin"
    if mode == "missing":
        source.unlink()
    elif mode == "extra":
        (root / "storage" / "extra.bin").write_bytes(b"extra")
    else:
        source.write_bytes(b"corrupt")
    with pytest.raises(RecoveryError, match="backup_storage_set_mismatch|backup_storage_integrity_failed"):
        validate_artifact(root)


def test_artifact_requires_manifest(tmp_path):
    root = artifact(tmp_path)
    (root / "manifest.json").unlink()
    with pytest.raises(RecoveryError, match="invalid_json_manifest"):
        validate_artifact(root)


def test_future_revision_is_rejected():
    manifest = valid_manifest()
    manifest["alembic_revision"] = "9999_future"
    with pytest.raises(RecoveryError, match="unknown_backup_revision"):
        require_known_revision(manifest, {"0062_signed_report_addendum_integrity"})
