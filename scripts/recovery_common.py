from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse


BACKUP_VERSION = 1
DATABASE_DUMP_NAME = "database.dump"
FILE_MANIFEST_NAME = "files.manifest.json"
MAIN_MANIFEST_NAME = "manifest.json"
STORAGE_DIRECTORY_NAME = "storage"
RECOVERY_MARKER_TABLE = "_astra_recovery_incomplete"
SAFE_RELATIVE_PART = re.compile(r"^[A-Za-z0-9._-]+$")
SENSITIVE_LOG_KEY = re.compile(r"password|secret|token|cookie|database.*url|filename|patient|oib|content", re.IGNORECASE)
SENSITIVE_LOG_VALUE = re.compile(r"postgres(?:ql)?(?:\+psycopg)?://|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY", re.IGNORECASE)


class RecoveryError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryError("invalid_json_manifest") from exc


def sha256_file(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise RecoveryError("artifact_read_failed") from exc
    return digest.hexdigest()


def safe_relative_path(raw: str) -> Path:
    candidate = Path(raw.replace("\\", "/"))
    if candidate.is_absolute() or not candidate.parts or any(part in {"", ".", ".."} or not SAFE_RELATIVE_PART.fullmatch(part) for part in candidate.parts):
        raise RecoveryError("unsafe_storage_path")
    return candidate


def resolved_child(root: Path, relative: Path) -> Path:
    resolved_root = root.resolve()
    candidate = (resolved_root / relative).resolve()
    if resolved_root not in candidate.parents:
        raise RecoveryError("unsafe_storage_path")
    return candidate


def postgres_environment(database_url: str) -> dict[str, str]:
    parsed = urlparse(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
    if parsed.scheme not in {"postgresql", "postgres"} or not parsed.hostname or not parsed.path.strip("/"):
        raise RecoveryError("invalid_database_url")
    environment = os.environ.copy()
    environment.update(
        {
            "PGHOST": parsed.hostname,
            "PGPORT": str(parsed.port or 5432),
            "PGUSER": unquote(parsed.username or ""),
            "PGDATABASE": unquote(parsed.path.lstrip("/")),
        }
    )
    if parsed.password is not None:
        environment["PGPASSWORD"] = unquote(parsed.password)
    query = parse_qs(parsed.query)
    if query.get("sslmode"):
        environment["PGSSLMODE"] = query["sslmode"][0]
    return environment


def run_postgres_tool(binary: str, arguments: list[str], database_url: str, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
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
        result = subprocess.run([binary, "--version"], check=True, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise RecoveryError("postgres_tool_not_found") from exc
    except subprocess.CalledProcessError as exc:
        raise RecoveryError("postgres_tool_version_failed") from exc
    return result.stdout.strip()


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
        **{key: _redacted_log_value(key, value) for key, value in safe_fields.items()},
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def require_database_url(environment_name: str) -> str:
    value = os.environ.get(environment_name)
    if not value:
        raise RecoveryError("database_url_environment_missing")
    return value


def validate_main_manifest(value: Any) -> dict[str, Any]:
    required = {
        "backup_version",
        "created_at",
        "application_commit",
        "alembic_revision",
        "postgres_server_version",
        "pg_dump_version",
        "dump_sha256",
        "file_storage_included",
        "file_manifest_sha256",
        "storage_object_count",
    }
    if not isinstance(value, dict) or set(value) != required or value.get("backup_version") != BACKUP_VERSION:
        raise RecoveryError("unsupported_backup_manifest")
    for key in required - {"backup_version", "file_storage_included", "storage_object_count"}:
        if not isinstance(value.get(key), str) or not value[key]:
            raise RecoveryError("invalid_backup_manifest")
    if value["file_storage_included"] is not True or not isinstance(value["storage_object_count"], int):
        raise RecoveryError("incomplete_backup_manifest")
    return value
