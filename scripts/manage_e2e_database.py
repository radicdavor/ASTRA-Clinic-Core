from __future__ import annotations

import argparse
import re
from urllib.parse import urlparse, urlunparse

import psycopg


VALID_DB_NAME = re.compile(r"^[a-zA-Z0-9_]+$")


def psycopg_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def database_name(url: str) -> str:
    parsed = urlparse(psycopg_url(url))
    name = parsed.path.lstrip("/")
    if not VALID_DB_NAME.match(name):
        raise SystemExit(f"Unsafe E2E database name: {name!r}")
    return name


def admin_url(url: str) -> str:
    parsed = urlparse(psycopg_url(url))
    return urlunparse(parsed._replace(path="/postgres"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or drop an isolated ASTRA E2E PostgreSQL database.")
    parser.add_argument("action", choices={"create", "drop"})
    parser.add_argument("database_url")
    args = parser.parse_args()

    db_name = database_name(args.database_url)
    with psycopg.connect(admin_url(args.database_url), autocommit=True) as connection:
        with connection.cursor() as cursor:
            if args.action == "create":
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                    (db_name,),
                )
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
                cursor.execute(f'CREATE DATABASE "{db_name}"')
            else:
                cursor.execute(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                    (db_name,),
                )
                cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')


if __name__ == "__main__":
    main()
