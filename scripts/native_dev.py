"""Run native development with the database identity resolved by Compose."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DB_KEYS = ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")


def compose_command(args: argparse.Namespace) -> list[str]:
    command = ["docker", "compose"]
    if args.project_name:
        command += ["--project-name", args.project_name]
    for path in args.compose_file:
        command += ["--file", str(Path(path).resolve())]
    return command


def resolved_identity(args: argparse.Namespace) -> tuple[dict[str, str], int]:
    result = subprocess.run(
        [*compose_command(args), "config", "--format", "json"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    service = json.loads(result.stdout).get("services", {}).get("db")
    if not isinstance(service, dict) or not isinstance(service.get("environment"), dict):
        raise RuntimeError("Compose must define a db service environment")
    values = {}
    for key in DB_KEYS:
        value = service["environment"].get(key)
        if not isinstance(value, str) or not value:
            raise RuntimeError(f"Compose requires non-empty {key}")
        values[key] = value
    ports = service.get("ports")
    if not isinstance(ports, list) or len(ports) != 1 or not isinstance(ports[0], dict):
        raise RuntimeError("Compose db must publish exactly one structured port")
    port = ports[0]
    if port.get("host_ip") != "127.0.0.1" or port.get("target") != 5432:
        raise RuntimeError("Compose db must publish PostgreSQL on loopback")
    try:
        published = int(port.get("published"))
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Compose db published port must be explicit") from exc
    if not 1 <= published <= 65535:
        raise RuntimeError("Compose db published port is invalid")
    return values, published


def database_url(values: dict[str, str], host: str, port: int) -> str:
    if host not in {"127.0.0.1", "db"}:
        raise RuntimeError("Development database host is not trusted")
    components = [quote(values[key], safe="") for key in DB_KEYS]
    database, user, password = components
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def safe_environment(url: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(APP_ENV="development", DEMO_MODE="true", REAL_DATA_ALLOWED="false", DATABASE_URL=url)
    return environment


def seed(args: argparse.Namespace) -> int:
    values, _ = resolved_identity(args)
    environment = safe_environment(database_url(values, "db", 5432))
    return subprocess.run(
        [*compose_command(args), "run", "--rm", "-e", "DATABASE_URL", "backend", "true"],
        cwd=ROOT, env=environment, check=False,
    ).returncode


def serve(args: argparse.Namespace) -> int:
    values, port = resolved_identity(args)
    storage = ROOT / ".astra-dev" / "documents"
    storage.mkdir(parents=True, exist_ok=True)
    environment = safe_environment(database_url(values, "127.0.0.1", port))
    environment["DOCUMENT_STORAGE_PATH"] = str(storage.resolve())
    return subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--app-dir", "backend", "--port", "8000"],
        cwd=ROOT, env=environment, check=False,
    ).returncode


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--project-name")
    result.add_argument("--compose-file", action="append", default=[])
    result.add_argument("command", choices=("seed", "serve"))
    return result


def main() -> int:
    args = parser().parse_args()
    return seed(args) if args.command == "seed" else serve(args)


if __name__ == "__main__":
    raise SystemExit(main())
