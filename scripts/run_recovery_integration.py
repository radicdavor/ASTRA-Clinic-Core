from __future__ import annotations

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import mkdtemp
from typing import Callable
from urllib.parse import quote, urlsplit, urlunsplit
from uuid import uuid4

import psycopg

from backup_postgres import create_backup, parser as backup_parser
from recovery_common import (
    FINAL_ALEMBIC_REVISION,
    SUPPORTED_BACKUP_REVISIONS,
    SYNTHETIC_ENVIRONMENT,
    RecoveryError,
    psycopg_url,
    read_alembic_revision,
    read_json,
    sha256_file,
    utc_now,
    write_json,
)
from restore_postgres import (
    DESTRUCTIVE_CONFIRMATION,
    _target_is_empty,
    parser as restore_parser,
    restore,
    validate_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
MEMBERSHIP_SCRIPT = ROOT / "scripts" / "validate_0057_clinic_membership_transition.py"
DOCUMENT_SCRIPT = ROOT / "scripts" / "validate_0063_document_provenance.py"
PREFIX = "membership-migration-"


def database_url(base_url: str, database_name: str) -> str:
    parsed = urlsplit(base_url.replace("postgresql+psycopg://", "postgresql://", 1))
    if parsed.hostname not in {"localhost", "127.0.0.1", "postgres"}:
        raise RecoveryError("recovery_admin_host_not_allowed")
    if parsed.path.lstrip("/") != "postgres":
        raise RecoveryError("recovery_admin_database_invalid")
    return urlunsplit(
        (
            "postgresql+psycopg",
            parsed.netloc,
            "/" + quote(database_name),
            parsed.query,
            "",
        )
    )


def _safe_database_name(name: str) -> None:
    if not name.startswith("astra_recovery_") or not all(
        character.isalnum() or character == "_" for character in name
    ):
        raise RecoveryError("unsafe_disposable_database_name")


def recreate_database(admin_url: str, name: str) -> None:
    _safe_database_name(name)
    with psycopg.connect(psycopg_url(admin_url), autocommit=True) as connection:
        connection.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname=%s AND pid<>pg_backend_pid()
            """,
            (name,),
        )
        connection.execute(f'DROP DATABASE IF EXISTS "{name}"')
        connection.execute(f'CREATE DATABASE "{name}"')


def drop_database(admin_url: str, name: str) -> None:
    _safe_database_name(name)
    with psycopg.connect(psycopg_url(admin_url), autocommit=True) as connection:
        connection.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname=%s AND pid<>pg_backend_pid()
            """,
            (name,),
        )
        connection.execute(f'DROP DATABASE IF EXISTS "{name}"')


def alembic(database: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database
    subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND,
        env=environment,
        check=True,
    )


def run_fixture_script(database: str, script: Path, action: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database
    subprocess.run(
        [sys.executable, str(script), action],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def prepare_source(database: str, revision: str, storage: Path) -> None:
    alembic(database, "upgrade", "0056_reception_note_patient_concurrency")
    run_fixture_script(database, MEMBERSHIP_SCRIPT, "seed-multi")
    alembic(database, "upgrade", "0062_signed_report_addendum_integrity")
    run_fixture_script(database, DOCUMENT_SCRIPT, "seed")
    if revision != "0062_signed_report_addendum_integrity":
        alembic(database, "upgrade", "0069_legacy_document_trust")
        run_fixture_script(
            database, MEMBERSHIP_SCRIPT, "seed-unsafe-ambiguous-memberships"
        )
        if revision != "0069_legacy_document_trust":
            alembic(database, "upgrade", revision)

    storage.mkdir()
    with psycopg.connect(psycopg_url(database)) as connection:
        connection.execute(
            """
            INSERT INTO permissions (name)
            VALUES
                ('documents.review'),
                ('clinical.documents.read_institution'),
                ('appointments.read')
            ON CONFLICT (name) DO NOTHING
            """
        )
        connection.execute(
            """
            UPDATE roles SET professional_category='medical_staff'
            WHERE id=(
                SELECT role_id FROM users WHERE email=%s
            )
            """,
            (f"{PREFIX}provider@example.invalid",),
        )
        connection.execute(
            """
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT u.role_id, p.id
            FROM users u CROSS JOIN permissions p
            WHERE u.email=%s
              AND p.name IN (
                  'documents.review',
                  'clinical.documents.read_institution',
                  'appointments.read'
              )
            ON CONFLICT DO NOTHING
            """,
            (f"{PREFIX}provider@example.invalid",),
        )
        actual_revision = read_alembic_revision(connection)
        if actual_revision != revision:
            raise RecoveryError("source_revision_preparation_failed")
        document_id = int(
            connection.execute(
                """
                SELECT id FROM clinical_documents
                WHERE title='PR3-MIGRATION-UNRESOLVED'
                """
            ).fetchone()[0]
        )
        relative = f"synthetic/{document_id}.bin"
        content = f"ASTRA-SYNTHETIC-RECOVERY-{revision}\n".encode()
        path = storage / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
        connection.execute(
            """
            UPDATE clinical_documents
            SET attachment_path=%s, file_size_bytes=%s, checksum_sha256=%s,
                mime_type='application/octet-stream'
            WHERE id=%s
            """,
            (relative, len(content), sha256(content).hexdigest(), document_id),
        )
        connection.execute(
            """
            INSERT INTO audit_logs
                (actor_type, action, entity_type, summary, request_id)
            VALUES
                ('system', 'synthetic_fixture_baseline', 'RecoveryValidation',
                 'Synthetic recovery audit sentinel', %s)
            """,
            (f"recovery-{revision}",),
        )
        if revision == FINAL_ALEMBIC_REVISION:
            patient_id = int(
                connection.execute(
                    "SELECT id FROM patients WHERE last_name=%s",
                    (f"{PREFIX}patient",),
                ).fetchone()[0]
            )
            institution_id = int(
                connection.execute(
                    "SELECT institution_id FROM clinics WHERE name=%s",
                    (f"{PREFIX}clinic-a",),
                ).fetchone()[0]
            )
            connection.execute(
                """
                INSERT INTO clinical_episodes
                    (patient_id, institution_id, title, start_date)
                VALUES (%s, %s, 'RECOVERY-SYNTHETIC-EPISODE', DATE '2026-07-27')
                """,
                (patient_id, institution_id),
            )
        connection.commit()


def _user_id(connection: psycopg.Connection, suffix: str) -> int:
    return int(
        connection.execute(
            "SELECT id FROM users WHERE email=%s",
            (f"{PREFIX}{suffix}@example.invalid",),
        ).fetchone()[0]
    )


def _membership_ids(connection: psycopg.Connection, suffix: str) -> list[int]:
    return [
        int(row[0])
        for row in connection.execute(
            """
            SELECT clinic_id FROM clinic_memberships
            WHERE user_id=%s AND active=true
            ORDER BY clinic_id
            """,
            (_user_id(connection, suffix),),
        ).fetchall()
    ]


def verify_membership_recovery(database: str, source_revision: str) -> None:
    with psycopg.connect(psycopg_url(database)) as connection:
        if read_alembic_revision(connection) != FINAL_ALEMBIC_REVISION:
            raise RecoveryError("membership_recovery_wrong_revision")
        if len(_membership_ids(connection, "provider")) != 1:
            raise RecoveryError("legitimate_membership_not_preserved")
        for suffix in (
            "ambiguous",
            "inactive-provider",
            "inactive-clinic",
            "invalid-provider",
            "duplicate-provider",
        ):
            if _membership_ids(connection, suffix):
                raise RecoveryError("unsafe_membership_reconstructed")
        reasons = {
            str(row[0])
            for row in connection.execute(
                "SELECT reason FROM clinic_membership_migration_issues"
            ).fetchall()
        }
        required = {
            "ambiguous_active_clinic_candidates",
            "no_clinic_candidate",
            "inactive_clinic_candidate",
            "invalid_provider_identity",
        }
        if not required.issubset(reasons):
            raise RecoveryError("membership_reason_taxonomy_lost")
        if source_revision != "0062_signed_report_addendum_integrity":
            if len(_membership_ids(connection, "manual-preserved")) != 1:
                raise RecoveryError("manual_membership_not_preserved")
            if len(_membership_ids(connection, "unrelated-preserved")) != 1:
                raise RecoveryError("unrelated_membership_not_preserved")
            corrected = int(
                connection.execute(
                    """
                    SELECT count(*) FROM clinic_membership_migration_issues
                    WHERE correction_reason='corrected_unsafe_automatic_membership'
                    """
                ).fetchone()[0]
            )
            if corrected < 1:
                raise RecoveryError("membership_correction_record_lost")


def verify_document_and_audit_recovery(database: str, request_id: str) -> None:
    with psycopg.connect(psycopg_url(database)) as connection:
        classifications = {
            str(row[0])
            for row in connection.execute(
                """
                SELECT record_classification FROM clinical_documents
                WHERE title LIKE 'PR3-MIGRATION-%'
                """
            ).fetchall()
        }
        if classifications != {"unclassified"}:
            raise RecoveryError("document_trust_escalated")
        unresolved = int(
            connection.execute(
                """
                SELECT count(*) FROM clinical_documents
                WHERE title='PR3-MIGRATION-UNRESOLVED'
                  AND record_classification='unclassified'
                  AND institution_id IS NULL
                """
            ).fetchone()[0]
        )
        if unresolved != 1:
            raise RecoveryError("document_provenance_changed")
        audit_rows = connection.execute(
            """
            SELECT action, entity_type, summary
            FROM audit_logs WHERE request_id=%s
            """,
            (request_id,),
        ).fetchall()
        if audit_rows != [
            (
                "synthetic_fixture_baseline",
                "RecoveryValidation",
                "Synthetic recovery audit sentinel",
            )
        ]:
            raise RecoveryError("audit_recovery_mismatch")
        false_events = int(
            connection.execute(
                """
                SELECT count(*) FROM audit_logs
                WHERE action IN ('backup_completed', 'restore_completed')
                """
            ).fetchone()[0]
        )
        if false_events:
            raise RecoveryError("recovery_created_false_user_audit")


def run_application_smoke(database: str, storage: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "DATABASE_URL": database,
            "DOCUMENT_STORAGE_PATH": str(storage),
            "JWT_SECRET": "synthetic-recovery-smoke-secret-not-production",
            "JWT_SECRET_KEY": "synthetic-recovery-smoke-secret-not-production",
            "APP_ENV": "test",
            "PYTHONPATH": str(BACKEND),
        }
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "recovery_application_smoke.py")],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def _backup(
    source_url: str,
    source_storage: Path,
    artifact: Path,
    pg_dump: str,
) -> None:
    os.environ["RECOVERY_SOURCE_DATABASE_URL"] = source_url
    arguments = [
        "--output",
        str(artifact),
        "--storage-root",
        str(source_storage),
        "--database-url-env",
        "RECOVERY_SOURCE_DATABASE_URL",
        "--pg-dump",
        pg_dump,
    ]
    create_backup(backup_parser().parse_args([*arguments, "--dry-run"]))
    create_backup(backup_parser().parse_args(arguments))


def _restore(
    target_url: str,
    target_storage: Path,
    artifact: Path,
    revision: str,
    pg_restore: str,
) -> dict[str, object]:
    os.environ["RECOVERY_TARGET_DATABASE_URL"] = target_url
    manifest_hash = validate_artifact(artifact)[2]
    arguments = [
        "--artifact",
        str(artifact),
        "--target-storage",
        str(target_storage),
        "--expected-source-revision",
        revision,
        "--expected-manifest-sha256",
        manifest_hash,
        "--database-url-env",
        "RECOVERY_TARGET_DATABASE_URL",
        "--pg-restore",
        pg_restore,
    ]
    if revision != FINAL_ALEMBIC_REVISION:
        arguments.append("--upgrade-head")
    restore(restore_parser().parse_args([*arguments, "--dry-run"]))
    return restore(
        restore_parser().parse_args(
            [
                *arguments,
                "--confirm-destructive",
                DESTRUCTIVE_CONFIRMATION,
            ]
        )
    )


def run_revision_scenario(
    admin_url: str,
    workspace: Path,
    revision: str,
    pg_dump: str,
    pg_restore: str,
    failing_pg_restore: str,
) -> dict[str, object]:
    suffix = uuid4().hex[:8]
    names = {
        "source": f"astra_recovery_source_{suffix}",
        "target": f"astra_recovery_target_{suffix}",
        "failed": f"astra_recovery_failed_{suffix}",
    }
    urls = {key: database_url(admin_url, name) for key, name in names.items()}
    source_storage = workspace / "source-storage"
    target_storage = workspace / "target-storage"
    artifact = workspace / "synthetic-backup"
    corrupt_artifact = workspace / "corrupt-backup"
    cleanup_completed = False
    try:
        for name in names.values():
            recreate_database(admin_url, name)
        prepare_source(urls["source"], revision, source_storage)
        _backup(urls["source"], source_storage, artifact, pg_dump)
        manifest, _entries, manifest_hash = validate_artifact(artifact)

        shutil.copytree(artifact, corrupt_artifact)
        with (corrupt_artifact / "database.dump").open("ab") as target:
            target.write(b"corruption")
        try:
            validate_artifact(corrupt_artifact)
        except RecoveryError as exc:
            if exc.code not in {"backup_size_mismatch", "backup_checksum_mismatch"}:
                raise
        else:
            raise RecoveryError("corrupt_backup_was_accepted")

        os.environ["RECOVERY_TARGET_DATABASE_URL"] = urls["failed"]
        failed_arguments = [
            "--artifact",
            str(artifact),
            "--target-storage",
            str(workspace / "failed-storage"),
            "--expected-source-revision",
            revision,
            "--expected-manifest-sha256",
            manifest_hash,
            "--database-url-env",
            "RECOVERY_TARGET_DATABASE_URL",
            "--pg-restore",
            failing_pg_restore,
            "--confirm-destructive",
            DESTRUCTIVE_CONFIRMATION,
        ]
        if revision != FINAL_ALEMBIC_REVISION:
            failed_arguments.append("--upgrade-head")
        try:
            restore(restore_parser().parse_args(failed_arguments))
        except RecoveryError as exc:
            if exc.code not in {"postgres_tool_failed", "postgres_tool_not_found"}:
                raise
        else:
            raise RecoveryError("failed_pg_restore_was_accepted")
        with psycopg.connect(psycopg_url(urls["failed"])) as connection:
            marker = connection.execute(
                "SELECT to_regclass('public._astra_recovery_incomplete')"
            ).fetchone()[0]
            if marker is None:
                raise RecoveryError("failed_restore_marker_missing")

        result = _restore(
            urls["target"],
            target_storage,
            artifact,
            revision,
            pg_restore,
        )
        verify_membership_recovery(urls["target"], revision)
        verify_document_and_audit_recovery(
            urls["target"], f"recovery-{revision}"
        )
        run_application_smoke(urls["target"], target_storage)

        try:
            _restore(
                urls["target"],
                target_storage,
                artifact,
                revision,
                pg_restore,
            )
        except RecoveryError as exc:
            if exc.code != "target_database_not_empty":
                raise
        else:
            raise RecoveryError("second_restore_overwrite_was_accepted")

        critical_count = len(manifest["semantic_snapshot"]["critical_tables"])
        return {
            "source_revision": revision,
            "restored_revision": result["restored_revision"],
            "final_revision": result["final_revision"],
            "backup_hash": result["backup_sha256"],
            "manifest_hash": manifest_hash,
            "semantic_checksum_count": critical_count,
            "membership_recovery": "passed",
            "document_provenance_recovery": "passed",
            "audit_recovery": "passed",
            "application_smoke": "passed",
            "cleanup_status": "completed",
        }
    finally:
        for name in names.values():
            drop_database(admin_url, name)
        cleanup_completed = True
        if not cleanup_completed:
            raise RecoveryError("scenario_cleanup_failed")


def run_empty_database_scenario(admin_url: str) -> str:
    name = f"astra_recovery_empty_{uuid4().hex[:8]}"
    url = database_url(admin_url, name)
    try:
        recreate_database(admin_url, name)
        alembic(url, "upgrade", FINAL_ALEMBIC_REVISION)
        with psycopg.connect(psycopg_url(url)) as connection:
            return read_alembic_revision(connection)
    finally:
        drop_database(admin_url, name)


def verify_non_empty_target_object_categories(admin_url: str) -> None:
    cases = {
        "table": "CREATE TABLE recovery_object (id integer)",
        "partitioned_table": (
            "CREATE TABLE recovery_object (id integer) PARTITION BY RANGE (id)"
        ),
        "view": "CREATE VIEW recovery_object AS SELECT 1 AS id",
        "materialized_view": (
            "CREATE MATERIALIZED VIEW recovery_object AS SELECT 1 AS id"
        ),
        "sequence": "CREATE SEQUENCE recovery_object",
        "function": (
            "CREATE FUNCTION recovery_object() RETURNS integer "
            "LANGUAGE SQL IMMUTABLE AS 'SELECT 1'"
        ),
        "enum": "CREATE TYPE recovery_object AS ENUM ('synthetic')",
        "domain": "CREATE DOMAIN recovery_object AS text CHECK (VALUE <> '')",
        "schema": "CREATE SCHEMA recovery_object",
        "multiple": (
            "CREATE SEQUENCE recovery_sequence; "
            "CREATE VIEW recovery_view AS SELECT 1 AS id"
        ),
    }
    clean_name = f"astra_recovery_object_clean_{uuid4().hex[:8]}"
    try:
        recreate_database(admin_url, clean_name)
        with psycopg.connect(
            psycopg_url(database_url(admin_url, clean_name))
        ) as connection:
            if not _target_is_empty(connection):
                raise RecoveryError("clean_target_reported_non_empty")
    finally:
        drop_database(admin_url, clean_name)
    for category, statement in cases.items():
        name = f"astra_recovery_object_{category}_{uuid4().hex[:8]}"
        try:
            recreate_database(admin_url, name)
            with psycopg.connect(
                psycopg_url(database_url(admin_url, name))
            ) as connection:
                connection.execute(statement)
                connection.commit()
                if _target_is_empty(connection):
                    raise RecoveryError(
                        f"non_empty_target_{category}_was_accepted"
                    )
        finally:
            drop_database(admin_url, name)


def _remove_workspace(workspace: Path) -> None:
    try:
        shutil.rmtree(workspace)
    except OSError as exc:
        raise RecoveryError("scenario_cleanup_failed") from exc
    if workspace.exists():
        raise RecoveryError("scenario_cleanup_failed")


def _run_with_verified_cleanup(
    workspace: Path,
    result_file: Path,
    operation: Callable[[], dict[str, object]],
) -> dict[str, object]:
    try:
        result = operation()
    except Exception as primary_error:
        try:
            _remove_workspace(workspace)
        except Exception as cleanup_error:
            cleanup_failure = (
                cleanup_error
                if isinstance(cleanup_error, RecoveryError)
                else RecoveryError("scenario_cleanup_failed")
            )
            raise ExceptionGroup(
                "recovery_and_cleanup_failed",
                [primary_error, cleanup_failure],
            ) from None
        raise
    _remove_workspace(workspace)
    result["cleanup_status"] = "completed"
    write_json(result_file, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run disposable PostgreSQL recovery validation for Alembic 0071"
    )
    parser.add_argument(
        "--admin-database-url-env", default="RECOVERY_ADMIN_DATABASE_URL"
    )
    parser.add_argument("--pg-dump", default="pg_dump")
    parser.add_argument("--pg-restore", default="pg_restore")
    parser.add_argument("--failing-pg-restore", default="/bin/false")
    parser.add_argument("--result-file", type=Path, required=True)
    args = parser.parse_args()
    admin_url = os.environ.get(args.admin_database_url_env, "")
    if not admin_url:
        raise RecoveryError("recovery_admin_database_url_missing")
    os.environ["ASTRA_RECOVERY_ENVIRONMENT"] = SYNTHETIC_ENVIRONMENT
    source_sha = os.environ.get("REMEDIATION_CHECKOUT_SHA", "")
    if len(source_sha) != 40:
        raise RecoveryError("recovery_source_sha_invalid")
    os.environ["ASTRA_APPLICATION_COMMIT"] = source_sha
    workspace = Path(mkdtemp(prefix="astra-recovery-"))
    started_at = utc_now()

    def run_matrix() -> dict[str, object]:
        empty_revision = run_empty_database_scenario(admin_url)
        verify_non_empty_target_object_categories(admin_url)
        scenarios = []
        for revision in sorted(SUPPORTED_BACKUP_REVISIONS):
            scenario_workspace = workspace / revision
            scenario_workspace.mkdir()
            scenarios.append(
                run_revision_scenario(
                    admin_url,
                    scenario_workspace,
                    revision,
                    args.pg_dump,
                    args.pg_restore,
                    args.failing_pg_restore,
                )
            )
        with psycopg.connect(psycopg_url(admin_url)) as connection:
            postgres_version = str(connection.info.server_version)
        return {
            "started_at": started_at,
            "completed_at": utc_now(),
            "postgresql_version": postgres_version,
            "empty_database_final_revision": empty_revision,
            "scenarios": scenarios,
            "test_ids": [
                "empty_database_to_0071",
                "0062_restore_and_roll_forward",
                "0069_restore_and_roll_forward",
                "0070_restore_and_roll_forward",
                "0071_backup_restore",
                "explicit_source_restored_final_revision",
                "semantic_checksums",
                "membership_fail_closed_recovery",
                "document_provenance_and_trust_recovery",
                "audit_recovery",
                "corrupt_backup_rejection",
                "failed_pg_restore_marker",
                "non_empty_target_rejection",
                "non_empty_user_object_categories",
                "application_smoke",
            ],
            "cleanup_status": "not_attempted",
        }

    result = _run_with_verified_cleanup(workspace, args.result_file, run_matrix)
    print(
        json.dumps(
            {
                "status": "passed",
                "scenarios": len(result["scenarios"]),
                "final_revision": result["empty_database_final_revision"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
