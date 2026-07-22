from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import mkdtemp
from urllib.parse import quote, urlsplit, urlunsplit
from uuid import uuid4

import psycopg

from backup_postgres import create_backup, parser as backup_parser
from recovery_common import RecoveryError, canonical_json_bytes, operation_log
from restore_postgres import parser as restore_parser, restore


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
INTEGRITY_TABLES = (
    "institutions",
    "clinics",
    "clinic_memberships",
    "patients",
    "patient_clinic_associations",
    "appointments",
    "patient_journeys",
    "journey_activities",
    "clinical_documents",
    "clinical_document_addenda",
    "signed_clinical_reports",
    "invoices",
    "invoice_lines",
    "payment_transactions",
    "audit_logs",
)


def database_url(base_url: str, database_name: str) -> str:
    parsed = urlsplit(base_url.replace("postgresql+psycopg://", "postgresql://", 1))
    return urlunsplit(("postgresql+psycopg", parsed.netloc, "/" + quote(database_name), parsed.query, ""))


def psycopg_url(value: str) -> str:
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def recreate_database(admin_url: str, name: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()", (name,))
        connection.execute(f'DROP DATABASE IF EXISTS "{name}"')
        connection.execute(f'CREATE DATABASE "{name}"')


def drop_database(admin_url: str, name: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()", (name,))
        connection.execute(f'DROP DATABASE IF EXISTS "{name}"')


def alembic(database: str, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database
    subprocess.run([sys.executable, "-m", "alembic", *arguments], cwd=BACKEND, env=environment, check=True)


def seed_source(database: str, seed_file: Path) -> dict[str, object]:
    environment = os.environ.copy()
    environment.update({"DATABASE_URL": database, "ASTRA_E2E_SEED_FILE": str(seed_file)})
    subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_full_stack_e2e.py")], cwd=ROOT, env=environment, check=True)
    return json.loads(seed_file.read_text(encoding="utf-8"))


def add_recovery_fixture(database: str, storage: Path, seed: dict[str, object]) -> None:
    document_ids = [
        int(seed["clinical"]["signedDocument"]),
        int(seed["clinical"]["financialSource"]),
        int(seed["clinical"]["unclassifiedSource"]),
    ]
    with psycopg.connect(psycopg_url(database)) as connection:
        for index, document_id in enumerate(document_ids, start=1):
            relative = f"{document_id}/{uuid4().hex}.bin"
            content = f"ASTRA-SYNTHETIC-RECOVERY-OBJECT-{index}\n".encode()
            path = storage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            connection.execute(
                """
                UPDATE clinical_documents
                SET attachment_path=%s, file_size_bytes=%s, checksum_sha256=%s,
                    mime_type='application/octet-stream', original_filename=%s
                WHERE id=%s
                """,
                (relative, len(content), sha256(content).hexdigest(), f"synthetic-{index}.bin", document_id),
            )

        user_id = connection.execute("SELECT id FROM users WHERE email='e2e.admin.a@example.invalid'").fetchone()[0]
        now = datetime.now(UTC)
        sessions = (
            ("recovery-active-session", now + timedelta(days=1), None),
            ("recovery-revoked-session", now + timedelta(days=1), now - timedelta(hours=1)),
            ("recovery-expired-session", now - timedelta(days=1), now - timedelta(days=2)),
        )
        for raw, expires_at, revoked_at in sessions:
            connection.execute(
                """
                INSERT INTO user_sessions (user_id, token_hash, csrf_token_hash, expires_at, revoked_at, last_seen_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, sha256(raw.encode()).hexdigest(), sha256((raw + "-csrf").encode()).hexdigest(), expires_at, revoked_at, now),
            )
        connection.execute(
            """
            INSERT INTO audit_logs (actor_type, action, entity_type, summary, request_id)
            VALUES ('system', 'recovery_fixture', 'RecoveryValidation', 'Synthetic recovery integrity sentinel', 'recovery-fixture')
            """
        )
        connection.commit()


def database_integrity(database: str) -> dict[str, object]:
    result: dict[str, object] = {}
    with psycopg.connect(psycopg_url(database)) as connection:
        for table in INTEGRITY_TABLES:
            rows = connection.execute(
                f"SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text), '[]'::jsonb) FROM \"{table}\" t"
            ).fetchone()[0]
            result[table] = sha256(canonical_json_bytes(rows)).hexdigest()
        result["alembic_revision"] = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        result["active_sessions"] = connection.execute(
            "SELECT count(*) FROM user_sessions WHERE revoked_at IS NULL AND expires_at > now()"
        ).fetchone()[0]
        leaked = connection.execute(
            "SELECT count(*) FROM audit_logs WHERE COALESCE(summary, '') LIKE '%ORIGINAL_CONTENT%'"
        ).fetchone()[0]
        if leaked:
            raise RecoveryError("clinical_content_found_in_audit")
    return result


def assert_restore_integrity(source: dict[str, object], target: dict[str, object]) -> None:
    for table in INTEGRITY_TABLES:
        if source[table] != target[table]:
            raise RecoveryError(f"integrity_mismatch_{table}")
    if source["alembic_revision"] != target["alembic_revision"]:
        raise RecoveryError("integrity_revision_mismatch")
    if source["active_sessions"] < 1 or target["active_sessions"] != 0:
        raise RecoveryError("session_revocation_failed")


def run_application_smoke(database: str, storage: Path, seed_file: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "DATABASE_URL": database,
            "DOCUMENT_STORAGE_PATH": str(storage),
            "JWT_SECRET": "synthetic-recovery-smoke-secret",
            "JWT_SECRET_KEY": "synthetic-recovery-smoke-secret",
            "APP_ENV": "test",
        }
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "recovery_application_smoke.py"), "--seed-file", str(seed_file)],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def run_current_revision_scenario(admin_url: str, workspace: Path, pg_dump: str, pg_restore: str) -> None:
    workspace.mkdir(parents=True)
    suffix = uuid4().hex[:8]
    source_name = f"astra_recovery_source_{suffix}"
    target_name = f"astra_recovery_target_{suffix}"
    source_url = database_url(admin_url, source_name)
    target_url = database_url(admin_url, target_name)
    source_storage = workspace / "source-storage"
    target_storage = workspace / "target-storage"
    artifact = workspace / "backup"
    seed_file = workspace / "seed.json"
    source_storage.mkdir()
    try:
        recreate_database(admin_url, source_name)
        recreate_database(admin_url, target_name)
        alembic(source_url, "upgrade", "head")
        seed = seed_source(source_url, seed_file)
        add_recovery_fixture(source_url, source_storage, seed)
        source_integrity = database_integrity(source_url)

        os.environ["RECOVERY_SOURCE_URL"] = source_url
        os.environ["RECOVERY_TARGET_URL"] = target_url
        if not os.environ.get("ASTRA_APPLICATION_COMMIT"):
            os.environ["ASTRA_APPLICATION_COMMIT"] = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True
            ).stdout.strip()
        backup_args = backup_parser().parse_args(
            ["--output", str(artifact), "--storage-root", str(source_storage), "--database-url-env", "RECOVERY_SOURCE_URL", "--pg-dump", pg_dump]
        )
        create_backup(backup_args)
        restore_args = restore_parser().parse_args(
            ["--artifact", str(artifact), "--target-storage", str(target_storage), "--database-url-env", "RECOVERY_TARGET_URL", "--pg-restore", pg_restore]
        )

        with psycopg.connect(psycopg_url(target_url)) as connection:
            connection.execute("CREATE TABLE recovery_non_empty_sentinel (id integer)")
            connection.commit()
        try:
            restore(restore_args)
        except RecoveryError as exc:
            if exc.code != "target_database_not_empty":
                raise
        else:
            raise RecoveryError("non_empty_target_was_accepted")
        recreate_database(admin_url, target_name)

        interrupted_args = restore_parser().parse_args(
            ["--artifact", str(artifact), "--target-storage", str(target_storage), "--database-url-env", "RECOVERY_TARGET_URL", "--pg-restore", "/bin/false"]
        )
        try:
            restore(interrupted_args)
        except RecoveryError as exc:
            if exc.code != "postgres_tool_failed":
                raise
        else:
            raise RecoveryError("interrupted_restore_was_accepted")
        with psycopg.connect(psycopg_url(target_url)) as connection:
            marker = connection.execute("SELECT to_regclass('public._astra_recovery_incomplete')").fetchone()[0]
            if marker is None:
                raise RecoveryError("interrupted_restore_marker_missing")
        recreate_database(admin_url, target_name)

        restore(restore_args)
        target_integrity = database_integrity(target_url)
        assert_restore_integrity(source_integrity, target_integrity)
        run_application_smoke(target_url, target_storage, seed_file)
    finally:
        drop_database(admin_url, source_name)
        drop_database(admin_url, target_name)


def run_old_revision_scenario(admin_url: str, workspace: Path, pg_dump: str, pg_restore: str, revision: str) -> None:
    workspace.mkdir(parents=True)
    suffix = uuid4().hex[:8]
    source_name = f"astra_recovery_old_source_{suffix}"
    target_name = f"astra_recovery_old_target_{suffix}"
    source_url = database_url(admin_url, source_name)
    target_url = database_url(admin_url, target_name)
    source_storage = workspace / "old-source-storage"
    target_storage = workspace / "old-target-storage"
    artifact = workspace / "old-backup"
    source_storage.mkdir()
    try:
        recreate_database(admin_url, source_name)
        recreate_database(admin_url, target_name)
        alembic(source_url, "upgrade", revision)
        os.environ["RECOVERY_OLD_SOURCE_URL"] = source_url
        os.environ["RECOVERY_OLD_TARGET_URL"] = target_url
        backup_args = backup_parser().parse_args(
            ["--output", str(artifact), "--storage-root", str(source_storage), "--database-url-env", "RECOVERY_OLD_SOURCE_URL", "--pg-dump", pg_dump]
        )
        create_backup(backup_args)
        restore_args = restore_parser().parse_args(
            ["--artifact", str(artifact), "--target-storage", str(target_storage), "--database-url-env", "RECOVERY_OLD_TARGET_URL", "--pg-restore", pg_restore, "--upgrade-head"]
        )
        restore(restore_args)
        with psycopg.connect(psycopg_url(target_url)) as connection:
            revision_row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
            if not revision_row or revision_row[0] != "0062_signed_report_addendum_integrity":
                raise RecoveryError("old_revision_upgrade_failed")
    finally:
        drop_database(admin_url, source_name)
        drop_database(admin_url, target_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run complete synthetic ASTRA backup/restore validation")
    parser.add_argument("--admin-database-url-env", default="RECOVERY_ADMIN_DATABASE_URL")
    parser.add_argument("--pg-dump", default="pg_dump")
    parser.add_argument("--pg-restore", default="pg_restore")
    parser.add_argument("--old-revision", default="0061_institution_model_clinical_record")
    args = parser.parse_args()
    admin_url = os.environ.get(args.admin_database_url_env)
    if not admin_url:
        raise RecoveryError("recovery_admin_database_url_missing")
    workspace = Path(mkdtemp(prefix="astra-recovery-"))
    operation_id = uuid4().hex
    operation_log(operation_id, "recovery_validation_started")
    try:
        run_current_revision_scenario(admin_url, workspace / "current", args.pg_dump, args.pg_restore)
        run_old_revision_scenario(admin_url, workspace / "old", args.pg_dump, args.pg_restore, args.old_revision)
        operation_log(operation_id, "recovery_validation_completed", scenarios=2)
        return 0
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
