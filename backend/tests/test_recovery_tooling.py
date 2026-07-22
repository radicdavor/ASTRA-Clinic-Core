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
)
from restore_postgres import validate_file_manifest  # noqa: E402
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
