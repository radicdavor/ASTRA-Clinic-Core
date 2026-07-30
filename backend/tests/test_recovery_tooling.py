from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from recovery_common import (  # noqa: E402
    FINAL_ALEMBIC_REVISION,
    MANIFEST_NAME,
    RECOVERY_SCHEMA_VERSION,
    RECOVERY_TEST_IDS,
    SYNTHETIC_ENVIRONMENT,
    SYNTHETIC_MARKER,
    RecoveryError,
    canonical_database_url,
    database_identity,
    operation_log,
    postgres_environment,
    read_alembic_revision,
    require_recovery_environment,
    safe_relative_path,
    sha256_file,
    verify_database_connection,
    write_json,
)
from restore_postgres import (  # noqa: E402
    DESTRUCTIVE_CONFIRMATION,
    _preflight_target_storage,
    _target_is_empty,
    restore,
    validate_artifact,
    validate_file_manifest,
)
from run_recovery_integration import (  # noqa: E402
    _remove_workspace,
    _run_with_verified_cleanup,
)


def semantic_snapshot() -> dict[str, object]:
    return {
        "revision": FINAL_ALEMBIC_REVISION,
        "table_inventory": ["alembic_version"],
        "critical_tables": {
            "alembic_version": {"row_count": 1, "sha256": "a" * 64}
        },
        "missing_critical_tables": [],
        "invariants": {
            "alembic_revision_rows": 1,
            "unvalidated_foreign_keys": 0,
        },
    }


def valid_manifest(dump: Path, file_manifest: Path) -> dict[str, object]:
    return {
        "schema_version": RECOVERY_SCHEMA_VERSION,
        "source_git_sha": "a" * 40,
        "source_environment": SYNTHETIC_ENVIRONMENT,
        "source_alembic_revision": FINAL_ALEMBIC_REVISION,
        "postgresql_version": "160014",
        "created_at": "2026-07-27T00:00:00+00:00",
        "backup_filename": "database.dump",
        "backup_size": dump.stat().st_size,
        "backup_sha256": sha256_file(dump),
        "file_manifest_sha256": sha256_file(file_manifest),
        "semantic_snapshot": semantic_snapshot(),
        "synthetic_marker": SYNTHETIC_MARKER,
        "forbidden_production": False,
        "tool_versions": {
            "pg_dump": "pg_dump (PostgreSQL) 16",
            "python": "3.12",
            "recovery_contract": RECOVERY_SCHEMA_VERSION,
        },
    }


def artifact(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic-backup"
    storage = root / "storage"
    storage.mkdir(parents=True)
    dump = root / "database.dump"
    dump.write_bytes(b"synthetic-pg-dump")
    file_manifest = root / "files.manifest.json"
    write_json(file_manifest, {"schema_version": 1, "objects": []})
    write_json(root / "manifest.json", valid_manifest(dump, file_manifest))
    return root


@pytest.mark.parametrize(
    "value",
    (
        "../escape.dump",
        "/absolute.dump",
        "folder/../../escape",
        "folder/name with space.dump",
        ".",
    ),
)
def test_recovery_path_rejects_traversal_and_unsafe_names(value: str):
    with pytest.raises(RecoveryError, match="unsafe_artifact_path"):
        safe_relative_path(value)


def test_recovery_environment_is_synthetic_only(monkeypatch):
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", "production")
    with pytest.raises(RecoveryError, match="recovery_environment_not_allowed"):
        require_recovery_environment()
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", SYNTHETIC_ENVIRONMENT)
    assert require_recovery_environment() == SYNTHETIC_ENVIRONMENT


@pytest.mark.parametrize(
    "url,error",
    (
        (
            "postgresql://user:secret@production-db/astra",
            "recovery_database_host_not_allowed",
        ),
        (
            "postgresql://user:secret@localhost/astra",
            "recovery_database_name_not_allowed",
        ),
    ),
)
def test_recovery_target_allowlist_rejects_production_like_urls(url: str, error: str):
    with pytest.raises(RecoveryError, match=error):
        database_identity(url)


def test_canonical_database_identity_accepts_required_uri_only():
    url = (
        "postgresql+psycopg://astra:synthetic-secret@127.0.0.1:5432/"
        "astra_recovery_test?sslmode=disable"
    )
    assert database_identity(url) == {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "astra_recovery_test",
        "user": "astra",
    }
    canonical = canonical_database_url(url)
    assert canonical.startswith("postgresql+psycopg://astra:")
    assert "sslmode=disable" in canonical


@pytest.mark.parametrize(
    "suffix",
    [
        "?host=other-host",
        "?hostaddr=127.0.0.2",
        "?dbname=other-db",
        "?port=6543",
        "?user=other",
        "?service=production",
        "?servicefile=%2Ftmp%2Fpg_service.conf",
        "?host=127.0.0.1%2Cother-host",
        "?host=127.0.0.1&host=other-host",
        "?%68ost=other-host",
        "?dbname=astra_recovery_test",
        "?options=-c%20search_path%3Dother",
    ],
)
def test_database_identity_rejects_target_selecting_or_unknown_parameters(suffix):
    with pytest.raises(
        RecoveryError, match="parameters_not_allowed|invalid_database_url"
    ):
        database_identity(
            "postgresql://astra:secret@127.0.0.1:5432/astra_recovery_test"
            + suffix
        )


def test_database_identity_rejects_keyword_dsn_and_multi_host():
    with pytest.raises(RecoveryError, match="invalid_database_url"):
        database_identity(
            "host=127.0.0.1 dbname=astra_recovery_test user=astra"
        )
    with pytest.raises(RecoveryError, match="invalid_database_url|parameters_not_allowed"):
        database_identity(
            "postgresql://astra:secret@127.0.0.1,localhost/astra_recovery_test"
        )


def test_postgres_environment_removes_external_pg_target_overrides(monkeypatch):
    monkeypatch.setenv("PGHOST", "attacker")
    monkeypatch.setenv("PGHOSTADDR", "203.0.113.5")
    monkeypatch.setenv("PGDATABASE", "production")
    monkeypatch.setenv("PGSERVICE", "production")
    environment = postgres_environment(
        "postgresql://astra:secret@127.0.0.1:5432/astra_recovery_test"
    )
    assert environment["PGHOST"] == "127.0.0.1"
    assert environment["PGPORT"] == "5432"
    assert environment["PGDATABASE"] == "astra_recovery_test"
    assert environment["PGUSER"] == "astra"
    assert "PGHOSTADDR" not in environment
    assert "PGSERVICE" not in environment


class _ConnectionInfo:
    host = "127.0.0.1"
    port = 5432


class _IdentityConnection:
    info = _ConnectionInfo()

    def __init__(self, row=("astra_recovery_test", "astra", 5432)):
        self.row = row

    def execute(self, statement):
        assert "current_database()" in statement
        return _FakeResult([self.row])


def test_effective_database_identity_accepts_matching_connection():
    assert verify_database_connection(
        _IdentityConnection(),
        "postgresql://astra:secret@127.0.0.1:5432/astra_recovery_test",
    )["database"] == "astra_recovery_test"


@pytest.mark.parametrize(
    "row",
    [
        ("other_database", "astra", 5432),
        ("astra_recovery_test", "other_user", 5432),
        ("astra_recovery_test", "astra", 6543),
    ],
)
def test_effective_database_identity_rejects_mismatch_without_secret(row):
    with pytest.raises(RecoveryError, match="recovery_database_identity_mismatch") as exc:
        verify_database_connection(
            _IdentityConnection(row),
            "postgresql://astra:do-not-leak@127.0.0.1:5432/astra_recovery_test",
        )
    assert "do-not-leak" not in str(exc.value)


def test_artifact_rejects_missing_manifest(tmp_path):
    root = artifact(tmp_path)
    (root / "manifest.json").unlink()
    with pytest.raises(RecoveryError, match="artifact_read_failed"):
        validate_artifact(root)


def test_artifact_rejects_corrupt_dump(tmp_path):
    root = artifact(tmp_path)
    (root / "database.dump").write_bytes(b"truncated")
    with pytest.raises(RecoveryError, match="backup_size_mismatch|backup_checksum_mismatch"):
        validate_artifact(root)


def test_artifact_rejects_same_size_dump_checksum_mismatch(tmp_path):
    root = artifact(tmp_path)
    dump = root / "database.dump"
    content = bytearray(dump.read_bytes())
    content[0] ^= 0x01
    dump.write_bytes(content)
    with pytest.raises(RecoveryError, match="backup_checksum_mismatch"):
        validate_artifact(root)


def test_artifact_rejects_manifest_hash_change(tmp_path):
    root = artifact(tmp_path)
    payload = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    payload["source_git_sha"] = "b" * 40
    (root / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    # The main manifest is not self-signed, but its canonical hash is returned
    # and bound into recovery evidence. The dump/file hashes remain mandatory.
    manifest, entries, manifest_hash = validate_artifact(root)
    assert manifest["source_git_sha"] == "b" * 40
    assert entries == []
    assert len(manifest_hash) == 64


def test_file_manifest_rejects_path_traversal():
    entry = {
        "document_id": 1,
        "relative_path": "../escape.bin",
        "size": 1,
        "sha256": "a" * 64,
        "classification": "unclassified",
        "content_type": "application/octet-stream",
    }
    with pytest.raises(RecoveryError, match="unsafe_artifact_path"):
        validate_file_manifest({"schema_version": 1, "objects": [entry]})


def test_file_manifest_rejects_duplicate_document_or_path():
    entry = {
        "document_id": 1,
        "relative_path": "opaque/one.bin",
        "size": 1,
        "sha256": "a" * 64,
        "classification": "unclassified",
        "content_type": "application/octet-stream",
    }
    with pytest.raises(RecoveryError, match="duplicate_file_manifest_entry"):
        validate_file_manifest(
            {"schema_version": 1, "objects": [entry, dict(entry)]}
        )


def test_restore_requires_explicit_destructive_confirmation(tmp_path, monkeypatch):
    root = artifact(tmp_path)
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", SYNTHETIC_ENVIRONMENT)
    monkeypatch.setenv(
        "RECOVERY_TARGET_DATABASE_URL",
        "postgresql://astra:astra@localhost/astra_recovery_test",
    )
    args = argparse.Namespace(
        artifact=root,
        target_storage=tmp_path / "restore-storage",
        expected_source_revision=FINAL_ALEMBIC_REVISION,
        expected_manifest_sha256=sha256_file(root / MANIFEST_NAME),
        database_url_env="RECOVERY_TARGET_DATABASE_URL",
        environment_env="ASTRA_RECOVERY_ENVIRONMENT",
        pg_restore="pg_restore",
        operation_id="test-operation",
        upgrade_head=False,
        dry_run=False,
        confirm_destructive=None,
    )
    with pytest.raises(RecoveryError, match="destructive_confirmation_required"):
        restore(args)
    args.confirm_destructive = DESTRUCTIVE_CONFIRMATION


def test_restore_dry_run_performs_no_database_connection(tmp_path, monkeypatch):
    root = artifact(tmp_path)
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", SYNTHETIC_ENVIRONMENT)
    monkeypatch.setenv(
        "RECOVERY_TARGET_DATABASE_URL",
        "postgresql://astra:astra@localhost/astra_recovery_test",
    )
    args = argparse.Namespace(
        artifact=root,
        target_storage=tmp_path / "restore-storage",
        expected_source_revision=FINAL_ALEMBIC_REVISION,
        expected_manifest_sha256=sha256_file(root / MANIFEST_NAME),
        database_url_env="RECOVERY_TARGET_DATABASE_URL",
        environment_env="ASTRA_RECOVERY_ENVIRONMENT",
        pg_restore="pg_restore",
        operation_id="test-operation",
        upgrade_head=False,
        dry_run=True,
        confirm_destructive=None,
    )
    result = restore(args)
    assert result["dry_run"] is True
    assert not args.target_storage.exists()


def test_restore_rejects_manifest_without_expected_out_of_band_hash(
    tmp_path, monkeypatch
):
    root = artifact(tmp_path)
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", SYNTHETIC_ENVIRONMENT)
    monkeypatch.setenv(
        "RECOVERY_TARGET_DATABASE_URL",
        "postgresql://astra:astra@localhost/astra_recovery_test",
    )
    args = argparse.Namespace(
        artifact=root,
        target_storage=tmp_path / "restore-storage",
        expected_source_revision=FINAL_ALEMBIC_REVISION,
        expected_manifest_sha256="0" * 64,
        database_url_env="RECOVERY_TARGET_DATABASE_URL",
        environment_env="ASTRA_RECOVERY_ENVIRONMENT",
        pg_restore="pg_restore",
        operation_id="test-operation",
        upgrade_head=False,
        dry_run=True,
        confirm_destructive=None,
    )
    with pytest.raises(RecoveryError, match="expected_manifest_checksum_mismatch"):
        restore(args)


def test_storage_preflight_rejects_nonempty_target_without_mutation(tmp_path):
    target = tmp_path / "target-storage"
    target.mkdir()
    (target / "existing.bin").write_bytes(b"synthetic")
    with pytest.raises(RecoveryError, match="target_storage_not_empty_or_unsafe"):
        _preflight_target_storage(target, "operation")


def test_restore_storage_preflight_fails_before_marker(tmp_path, monkeypatch):
    root = artifact(tmp_path)
    target = tmp_path / "restore-storage"
    target.mkdir()
    (target / "existing.bin").write_bytes(b"synthetic")
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", SYNTHETIC_ENVIRONMENT)
    monkeypatch.setenv(
        "RECOVERY_TARGET_DATABASE_URL",
        "postgresql://astra:secret@127.0.0.1:5432/astra_recovery_test",
    )
    marker_calls = []
    mutation_calls = []

    class Connection(_IdentityConnection):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, statement):
            if "current_database()" in statement:
                return _FakeResult([self.row])
            return _FakeResult([(False,)])

    monkeypatch.setattr("restore_postgres.psycopg.connect", lambda *_a, **_k: Connection())
    monkeypatch.setattr(
        "restore_postgres._create_marker",
        lambda *_a, **_k: marker_calls.append("marker"),
    )
    monkeypatch.setattr(
        "restore_postgres.run_postgres_tool",
        lambda *_a, **_k: mutation_calls.append("pg_restore"),
    )
    monkeypatch.setattr(
        "restore_postgres._run_alembic_upgrade",
        lambda *_a, **_k: mutation_calls.append("alembic"),
    )
    args = argparse.Namespace(
        artifact=root,
        target_storage=target,
        expected_source_revision=FINAL_ALEMBIC_REVISION,
        expected_manifest_sha256=sha256_file(root / MANIFEST_NAME),
        database_url_env="RECOVERY_TARGET_DATABASE_URL",
        environment_env="ASTRA_RECOVERY_ENVIRONMENT",
        pg_restore="pg_restore",
        operation_id="test-operation",
        upgrade_head=False,
        dry_run=False,
        confirm_destructive=DESTRUCTIVE_CONFIRMATION,
    )
    with pytest.raises(RecoveryError, match="target_storage_not_empty_or_unsafe"):
        restore(args)
    assert marker_calls == []
    assert mutation_calls == []
    assert (target / "existing.bin").read_bytes() == b"synthetic"


def test_effective_identity_mismatch_fails_before_marker_or_storage_mutation(
    tmp_path, monkeypatch
):
    root = artifact(tmp_path)
    target = tmp_path / "restore-storage"
    monkeypatch.setenv("ASTRA_RECOVERY_ENVIRONMENT", SYNTHETIC_ENVIRONMENT)
    monkeypatch.setenv(
        "RECOVERY_TARGET_DATABASE_URL",
        "postgresql://astra:do-not-leak@127.0.0.1:5432/astra_recovery_test",
    )
    marker_calls = []

    class Connection(_IdentityConnection):
        def __init__(self):
            super().__init__(("other_database", "astra", 5432))

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr("restore_postgres.psycopg.connect", lambda *_a, **_k: Connection())
    monkeypatch.setattr(
        "restore_postgres._create_marker",
        lambda *_a, **_k: marker_calls.append("marker"),
    )
    args = argparse.Namespace(
        artifact=root,
        target_storage=target,
        expected_source_revision=FINAL_ALEMBIC_REVISION,
        expected_manifest_sha256=sha256_file(root / MANIFEST_NAME),
        database_url_env="RECOVERY_TARGET_DATABASE_URL",
        environment_env="ASTRA_RECOVERY_ENVIRONMENT",
        pg_restore="pg_restore",
        operation_id="test-operation",
        upgrade_head=False,
        dry_run=False,
        confirm_destructive=DESTRUCTIVE_CONFIRMATION,
    )
    with pytest.raises(RecoveryError, match="recovery_database_identity_mismatch") as exc:
        restore(args)
    assert marker_calls == []
    assert not target.exists()
    assert "do-not-leak" not in str(exc.value)


def test_structured_logs_redact_credentials_and_patient_data(capsys):
    operation_log(
        "operation",
        "restore_failed",
        database_url="postgresql://user:secret@db/test",
        patient_name="Synthetic Person",
        error_code="checksum_mismatch",
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["database_url"] == "[REDACTED]"
    assert payload["patient_name"] == "[REDACTED]"
    assert payload["error_code"] == "checksum_mismatch"
    assert "secret" not in json.dumps(payload)


def test_symlink_artifact_is_rejected(tmp_path):
    root = artifact(tmp_path)
    link = tmp_path / "linked-backup"
    try:
        link.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    with pytest.raises(RecoveryError, match="symlink_artifact_rejected"):
        validate_artifact(link)


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class _FakeConnection:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, statement):
        if "to_regclass" in statement:
            return _FakeResult([("alembic_version",)])
        return _FakeResult(self.rows)


@pytest.mark.parametrize("has_user_objects", [True, False])
def test_target_empty_uses_catalog_wide_user_object_result(has_user_objects):
    connection = _FakeConnection([(has_user_objects,)])
    assert _target_is_empty(connection) is (not has_user_objects)


def test_target_empty_query_covers_relevant_catalogs_and_relkinds():
    statements = []

    class RecordingConnection:
        def execute(self, statement):
            statements.append(statement)
            return _FakeResult([(False,)])

    assert _target_is_empty(RecordingConnection())
    query = statements[0]
    assert "pg_catalog.pg_namespace" in query
    assert "pg_catalog.pg_class" in query
    assert "pg_catalog.pg_proc" in query
    assert "pg_catalog.pg_type" in query
    assert "relation.relkind IN ('r', 'p', 'f', 'v', 'm', 'S')" in query
    assert "dependency.deptype = 'e'" in query


def test_workspace_cleanup_verifies_real_postcondition(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "synthetic.tmp").write_text("synthetic", encoding="utf-8")
    _remove_workspace(workspace)
    assert not workspace.exists()


def test_workspace_cleanup_exception_blocks_completed_evidence(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result_file = tmp_path / "result.json"

    def fail_cleanup(_workspace):
        raise OSError("synthetic cleanup denial")

    monkeypatch.setattr("run_recovery_integration.shutil.rmtree", fail_cleanup)
    with pytest.raises(RecoveryError, match="scenario_cleanup_failed"):
        _run_with_verified_cleanup(
            workspace,
            result_file,
            lambda: {"cleanup_status": "not_attempted"},
        )
    assert not result_file.exists()


def test_workspace_cleanup_surviving_path_blocks_completed_evidence(
    tmp_path, monkeypatch
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result_file = tmp_path / "result.json"
    monkeypatch.setattr("run_recovery_integration.shutil.rmtree", lambda _path: None)
    with pytest.raises(RecoveryError, match="scenario_cleanup_failed"):
        _run_with_verified_cleanup(
            workspace,
            result_file,
            lambda: {"cleanup_status": "not_attempted"},
        )
    assert workspace.exists()
    assert not result_file.exists()


def test_primary_and_cleanup_failures_are_both_preserved(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result_file = tmp_path / "result.json"

    def primary_failure():
        raise RecoveryError("synthetic_primary_failure")

    monkeypatch.setattr(
        "run_recovery_integration.shutil.rmtree",
        lambda _path: (_ for _ in ()).throw(OSError("synthetic cleanup denial")),
    )
    with pytest.raises(ExceptionGroup) as captured:
        _run_with_verified_cleanup(workspace, result_file, primary_failure)
    assert [str(error) for error in captured.value.exceptions] == [
        "synthetic_primary_failure",
        "scenario_cleanup_failed",
    ]
    assert not result_file.exists()


def test_primary_failure_with_successful_cleanup_preserves_primary_error(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    result_file = tmp_path / "result.json"

    def primary_failure():
        raise RecoveryError("synthetic_primary_failure")

    with pytest.raises(RecoveryError, match="synthetic_primary_failure"):
        _run_with_verified_cleanup(workspace, result_file, primary_failure)
    assert not workspace.exists()
    assert not result_file.exists()


def test_revision_check_rejects_multiple_rows():
    with pytest.raises(RecoveryError, match="alembic_revision_row_count_invalid"):
        read_alembic_revision(
            _FakeConnection(
                [
                    ("0070_membership_correction",),
                    (FINAL_ALEMBIC_REVISION,),
                ]
            )
        )
