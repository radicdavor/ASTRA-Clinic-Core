from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Any, BinaryIO, Iterator
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse

from psycopg import Error as PsycopgError
from psycopg.conninfo import conninfo_to_dict

RECOVERY_SCHEMA_VERSION = 2
RECOVERY_EVIDENCE_SCHEMA_VERSION = 1
FINAL_ALEMBIC_REVISION = "0071_membership_taxonomy"
SUPPORTED_BACKUP_REVISIONS = frozenset(
    {
        "0062_signed_report_addendum_integrity",
        "0069_legacy_document_trust",
        "0070_membership_correction",
        FINAL_ALEMBIC_REVISION,
    }
)
SYNTHETIC_ENVIRONMENT = "synthetic-test"
SYNTHETIC_MARKER = "ASTRA_SYNTHETIC_RECOVERY_V1"
DATABASE_DUMP_NAME = "database.dump"
MANIFEST_NAME = "manifest.json"
FILE_MANIFEST_NAME = "files.manifest.json"
STORAGE_DIRECTORY_NAME = "storage"
RECOVERY_MARKER_TABLE = "_astra_recovery_incomplete"
SAFE_RELATIVE_PART = re.compile(r"^[A-Za-z0-9._-]+$")
SAFE_DATABASE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_TEST_DATABASE = re.compile(r"(?:test|ci|synthetic|recovery|restore)", re.IGNORECASE)
SENSITIVE_LOG_KEY = re.compile(
    r"password|secret|token|cookie|database.*url|patient|oib|content",
    re.IGNORECASE,
)
SENSITIVE_LOG_VALUE = re.compile(
    r"postgres(?:ql)?(?:\+psycopg)?://|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
    re.IGNORECASE,
)

CRITICAL_TABLES = (
    "alembic_version",
    "users",
    "institutions",
    "clinics",
    "clinic_memberships",
    "clinic_membership_migration_issues",
    "patients",
    "appointments",
    "clinical_documents",
    "audit_logs",
)
RECOVERY_TEST_IDS = (
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
)
ALLOWED_DATABASE_QUERY_PARAMETERS = frozenset({"sslmode"})
ALLOWED_SSL_MODES = frozenset(
    {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
)


class RecoveryError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _regular_file_handle(path: Path) -> BinaryIO:
    if path.is_symlink():
        raise RecoveryError("symlink_artifact_rejected")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RecoveryError("artifact_read_failed") from exc
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise RecoveryError("artifact_not_regular_file")
    return os.fdopen(descriptor, "rb")


def read_regular_bytes(path: Path) -> bytes:
    with _regular_file_handle(path) as source:
        return source.read()


def read_json(path: Path) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RecoveryError("duplicate_json_key")
            result[key] = value
        return result

    try:
        return json.loads(
            read_regular_bytes(path).decode("utf-8"),
            object_pairs_hook=unique_object,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryError("invalid_json_manifest") from exc


def sha256_file(path: Path) -> str:
    digest = sha256()
    with _regular_file_handle(path) as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verified_private_copy(source_path: Path, destination: Path, expected_hash: str) -> str:
    """Hash and copy one already-opened regular file to close hash/restore TOCTOU."""
    digest = sha256()
    with _regular_file_handle(source_path) as source, destination.open("xb") as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            target.write(chunk)
    actual = digest.hexdigest()
    if actual != expected_hash:
        destination.unlink(missing_ok=True)
        raise RecoveryError("backup_checksum_mismatch")
    return actual


def safe_relative_path(raw: str) -> Path:
    candidate = Path(raw.replace("\\", "/"))
    if (
        candidate.is_absolute()
        or not candidate.parts
        or any(
            part in {"", ".", ".."} or not SAFE_RELATIVE_PART.fullmatch(part)
            for part in candidate.parts
        )
    ):
        raise RecoveryError("unsafe_artifact_path")
    return candidate


def resolved_child(root: Path, relative: Path) -> Path:
    if root.is_symlink():
        raise RecoveryError("symlink_artifact_rejected")
    resolved_root = root.resolve()
    unresolved = resolved_root
    for part in relative.parts:
        unresolved = unresolved / part
        if unresolved.is_symlink():
            raise RecoveryError("symlink_artifact_rejected")
    candidate = unresolved.resolve()
    if candidate == resolved_root or resolved_root not in candidate.parents:
        raise RecoveryError("unsafe_artifact_path")
    return candidate


def require_safe_artifact_root(path: Path, *, must_exist: bool) -> Path:
    if path.is_symlink():
        raise RecoveryError("symlink_artifact_rejected")
    resolved = path.resolve()
    if must_exist and not resolved.is_dir():
        raise RecoveryError("backup_artifact_missing")
    if resolved.name in {"", ".", ".."} or not SAFE_RELATIVE_PART.fullmatch(resolved.name):
        raise RecoveryError("unsafe_artifact_path")
    return resolved


def require_recovery_environment(environment_name: str = "ASTRA_RECOVERY_ENVIRONMENT") -> str:
    value = os.environ.get(environment_name, "").strip()
    if value != SYNTHETIC_ENVIRONMENT:
        raise RecoveryError("recovery_environment_not_allowed")
    return value


def require_database_url(environment_name: str) -> str:
    value = os.environ.get(environment_name, "").strip()
    if not value:
        raise RecoveryError("database_url_environment_missing")
    return value


def _database_descriptor(database_url: str) -> dict[str, str | int | None]:
    normalized = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    if not normalized.startswith(("postgresql://", "postgres://")):
        raise RecoveryError("invalid_database_url")
    parsed = urlparse(normalized)
    try:
        parsed_port = parsed.port
        libpq = conninfo_to_dict(normalized)
    except (TypeError, ValueError, UnicodeError, PsycopgError) as exc:
        raise RecoveryError("invalid_database_url") from exc
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query_keys = [key for key, _value in query_pairs]
    if (
        parsed.scheme not in {"postgresql", "postgres"}
        or parsed.params
        or parsed.fragment
        or len(query_keys) != len(set(query_keys))
        or any(key not in ALLOWED_DATABASE_QUERY_PARAMETERS for key in query_keys)
    ):
        raise RecoveryError("recovery_database_parameters_not_allowed")
    allowed_libpq = {"host", "port", "dbname", "user", "password", "sslmode"}
    if set(libpq) - allowed_libpq:
        raise RecoveryError("recovery_database_parameters_not_allowed")
    host = str(libpq.get("host") or "")
    database = str(libpq.get("dbname") or "")
    user = str(libpq.get("user") or "")
    if (
        not host
        or "," in host
        or not database
        or not user
        or parsed.username is None
        or parsed.path.count("/") != 1
    ):
        raise RecoveryError("invalid_database_url")
    if host not in {"localhost", "127.0.0.1", "postgres"}:
        raise RecoveryError("recovery_database_host_not_allowed")
    if not SAFE_DATABASE_NAME.fullmatch(database) or not SAFE_TEST_DATABASE.search(database):
        raise RecoveryError("recovery_database_name_not_allowed")
    port_raw = libpq.get("port") or parsed_port or 5432
    try:
        port = int(port_raw)
    except (TypeError, ValueError) as exc:
        raise RecoveryError("invalid_database_url") from exc
    if not 1 <= port <= 65535:
        raise RecoveryError("invalid_database_url")
    sslmode = libpq.get("sslmode")
    if sslmode is not None and sslmode not in ALLOWED_SSL_MODES:
        raise RecoveryError("recovery_database_parameters_not_allowed")
    return {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": unquote(parsed.password) if parsed.password is not None else None,
        "sslmode": str(sslmode) if sslmode is not None else None,
    }


def database_identity(database_url: str) -> dict[str, str | int]:
    descriptor = _database_descriptor(database_url)
    return {
        "host": str(descriptor["host"]),
        "port": int(descriptor["port"]),
        "database": str(descriptor["database"]),
        "user": str(descriptor["user"]),
    }


def canonical_database_url(database_url: str) -> str:
    descriptor = _database_descriptor(database_url)
    credentials = quote(str(descriptor["user"]), safe="")
    if descriptor["password"] is not None:
        credentials += ":" + quote(str(descriptor["password"]), safe="")
    query = (
        urlencode({"sslmode": descriptor["sslmode"]})
        if descriptor["sslmode"] is not None
        else ""
    )
    return (
        f"postgresql+psycopg://{credentials}@{descriptor['host']}:{descriptor['port']}/"
        f"{quote(str(descriptor['database']), safe='')}"
        + (f"?{query}" if query else "")
    )


def verify_database_connection(connection: Any, database_url: str) -> dict[str, str | int]:
    expected = database_identity(database_url)
    info = connection.info
    try:
        row = connection.execute(
            "SELECT current_database(), current_user, inet_server_port()"
        ).fetchone()
    except Exception as exc:
        raise RecoveryError("recovery_database_identity_unavailable") from exc
    actual = {
        "host": str(info.host or ""),
        "port": int(info.port),
        "database": str(row[0]),
        "user": str(row[1]),
        "server_port": int(row[2]),
    }
    if (
        actual["host"] != expected["host"]
        or actual["port"] != expected["port"]
        or actual["server_port"] != expected["port"]
        or actual["database"] != expected["database"]
        or actual["user"] != expected["user"]
    ):
        raise RecoveryError("recovery_database_identity_mismatch")
    return expected


def postgres_environment(database_url: str) -> dict[str, str]:
    descriptor = _database_descriptor(database_url)
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("PG")
    }
    environment.update(
        {
            "PGHOST": str(descriptor["host"]),
            "PGPORT": str(descriptor["port"]),
            "PGUSER": str(descriptor["user"]),
            "PGDATABASE": str(descriptor["database"]),
        }
    )
    if descriptor["password"] is not None:
        environment["PGPASSWORD"] = str(descriptor["password"])
    if descriptor["sslmode"] is not None:
        environment["PGSSLMODE"] = str(descriptor["sslmode"])
    return environment


def psycopg_url(value: str) -> str:
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def run_postgres_tool(
    binary: str,
    arguments: list[str],
    database_url: str,
    *,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [binary, *arguments],
            env=postgres_environment(database_url),
            check=True,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        raise RecoveryError("postgres_tool_not_found") from exc
    except subprocess.CalledProcessError as exc:
        raise RecoveryError("postgres_tool_failed") from exc


def tool_version(binary: str) -> str:
    try:
        result = subprocess.run(
            [binary, "--version"], check=True, text=True, capture_output=True
        )
    except FileNotFoundError as exc:
        raise RecoveryError("postgres_tool_not_found") from exc
    except subprocess.CalledProcessError as exc:
        raise RecoveryError("postgres_tool_version_failed") from exc
    return result.stdout.strip()


def read_alembic_revision(connection: Any) -> str:
    table = connection.execute(
        "SELECT to_regclass('public.alembic_version')"
    ).fetchone()
    if not table or table[0] is None:
        raise RecoveryError("alembic_revision_missing")
    rows = connection.execute(
        "SELECT version_num FROM alembic_version ORDER BY version_num"
    ).fetchall()
    if len(rows) != 1:
        raise RecoveryError("alembic_revision_row_count_invalid")
    revision = str(rows[0][0])
    if revision not in SUPPORTED_BACKUP_REVISIONS:
        raise RecoveryError("unsupported_alembic_revision")
    return revision


def public_tables(connection: Any) -> list[str]:
    return [
        str(row[0])
        for row in connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ).fetchall()
        if str(row[0]) != RECOVERY_MARKER_TABLE
    ]


def _table_projection(connection: Any, table: str) -> dict[str, Any]:
    # Table names originate in pg_catalog. Quote them as identifiers anyway so a
    # crafted archive cannot turn an unusual table name into executable SQL.
    quoted_table = '"' + table.replace('"', '""') + '"'
    row_count = int(
        connection.execute(f"SELECT count(*) FROM {quoted_table}").fetchone()[0]
    )
    canonical_rows = connection.execute(
        f"""
        SELECT COALESCE(
            jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text),
            '[]'::jsonb
        )
        FROM {quoted_table} t
        """
    ).fetchone()[0]
    return {
        "row_count": row_count,
        "sha256": sha256_bytes(canonical_json_bytes(canonical_rows)),
    }


def invariant_checks(connection: Any, tables: set[str]) -> dict[str, int]:
    checks: dict[str, int] = {
        "alembic_revision_rows": int(
            connection.execute("SELECT count(*) FROM alembic_version").fetchone()[0]
        ),
        "unvalidated_foreign_keys": int(
            connection.execute(
                """
                SELECT count(*) FROM pg_constraint
                WHERE contype='f' AND connamespace='public'::regnamespace
                  AND NOT convalidated
                """
            ).fetchone()[0]
        ),
    }
    if "clinic_memberships" in tables:
        checks["duplicate_clinic_memberships"] = int(
            connection.execute(
                """
                SELECT count(*) FROM (
                    SELECT user_id, clinic_id
                    FROM clinic_memberships
                    GROUP BY user_id, clinic_id HAVING count(*) > 1
                ) duplicates
                """
            ).fetchone()[0]
        )
    document_columns: set[str] = set()
    if "clinical_documents" in tables:
        document_columns = {
            str(row[0])
            for row in connection.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public'
                  AND table_name='clinical_documents'
                """
            ).fetchall()
        }
    if (
        {"clinical_documents", "institutions"}.issubset(tables)
        and "institution_id" in document_columns
    ):
        checks["orphaned_document_institutions"] = int(
            connection.execute(
                """
                SELECT count(*) FROM clinical_documents d
                LEFT JOIN institutions i ON i.id=d.institution_id
                WHERE d.institution_id IS NOT NULL AND i.id IS NULL
                """
            ).fetchone()[0]
        )
    return checks


def semantic_snapshot(connection: Any) -> dict[str, Any]:
    tables = public_tables(connection)
    table_set = set(tables)
    critical = {
        table: _table_projection(connection, table)
        for table in CRITICAL_TABLES
        if table in table_set
    }
    missing = sorted(set(CRITICAL_TABLES) - table_set)
    revision = read_alembic_revision(connection)
    return {
        "revision": revision,
        "table_inventory": tables,
        "critical_tables": critical,
        "missing_critical_tables": missing,
        "invariants": invariant_checks(connection, table_set),
    }


def validate_snapshot(snapshot: Any) -> dict[str, Any]:
    required = {
        "revision",
        "table_inventory",
        "critical_tables",
        "missing_critical_tables",
        "invariants",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != required:
        raise RecoveryError("invalid_semantic_snapshot")
    if snapshot["revision"] not in SUPPORTED_BACKUP_REVISIONS:
        raise RecoveryError("unsupported_alembic_revision")
    if (
        not isinstance(snapshot["table_inventory"], list)
        or not isinstance(snapshot["critical_tables"], dict)
        or not isinstance(snapshot["missing_critical_tables"], list)
        or not isinstance(snapshot["invariants"], dict)
    ):
        raise RecoveryError("invalid_semantic_snapshot")
    for projection in snapshot["critical_tables"].values():
        if (
            not isinstance(projection, dict)
            or set(projection) != {"row_count", "sha256"}
            or not isinstance(projection["row_count"], int)
            or not isinstance(projection["sha256"], str)
            or len(projection["sha256"]) != 64
        ):
            raise RecoveryError("invalid_semantic_snapshot")
    return snapshot


def validate_main_manifest(value: Any) -> dict[str, Any]:
    required = {
        "schema_version",
        "source_git_sha",
        "source_environment",
        "source_alembic_revision",
        "postgresql_version",
        "created_at",
        "backup_filename",
        "backup_size",
        "backup_sha256",
        "file_manifest_sha256",
        "semantic_snapshot",
        "synthetic_marker",
        "forbidden_production",
        "tool_versions",
    }
    if (
        not isinstance(value, dict)
        or set(value) != required
        or value.get("schema_version") != RECOVERY_SCHEMA_VERSION
    ):
        raise RecoveryError("unsupported_backup_manifest")
    if (
        value.get("source_environment") != SYNTHETIC_ENVIRONMENT
        or value.get("synthetic_marker") != SYNTHETIC_MARKER
        or value.get("forbidden_production") is not False
    ):
        raise RecoveryError("backup_environment_not_allowed")
    if value.get("source_alembic_revision") not in SUPPORTED_BACKUP_REVISIONS:
        raise RecoveryError("unsupported_alembic_revision")
    safe_relative_path(str(value.get("backup_filename", "")))
    if value["backup_filename"] != DATABASE_DUMP_NAME:
        raise RecoveryError("unsafe_artifact_path")
    if not isinstance(value.get("backup_size"), int) or value["backup_size"] < 1:
        raise RecoveryError("invalid_backup_manifest")
    for key in (
        "source_git_sha",
        "postgresql_version",
        "created_at",
        "backup_sha256",
        "file_manifest_sha256",
    ):
        if not isinstance(value.get(key), str) or not value[key]:
            raise RecoveryError("invalid_backup_manifest")
    if len(value["source_git_sha"]) != 40 or any(
        character not in "0123456789abcdef"
        for character in value["source_git_sha"].lower()
    ):
        raise RecoveryError("invalid_backup_manifest")
    if len(value["backup_sha256"]) != 64 or len(value["file_manifest_sha256"]) != 64:
        raise RecoveryError("invalid_backup_manifest")
    if not isinstance(value.get("tool_versions"), dict):
        raise RecoveryError("invalid_backup_manifest")
    validate_snapshot(value.get("semantic_snapshot"))
    return value


def _redacted_log_value(key: str, value: Any) -> Any:
    if SENSITIVE_LOG_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, str) and SENSITIVE_LOG_VALUE.search(value):
        return "[REDACTED]"
    return value


def operation_log(operation_id: str, event: str, **safe_fields: Any) -> None:
    payload = {
        "operation_id": operation_id,
        "event": event,
        "at": utc_now(),
        **{
            key: _redacted_log_value(key, value)
            for key, value in safe_fields.items()
        },
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


@contextmanager
def recovery_failure_log(
    operation_id: str, event_prefix: str
) -> Iterator[None]:
    try:
        yield
    except Exception as exc:
        code = exc.code if isinstance(exc, RecoveryError) else f"unexpected_{event_prefix}_failure"
        operation_log(operation_id, f"{event_prefix}_failed", error_code=code)
        raise
