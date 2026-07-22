from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from app.core.database import SessionLocal
from app.services.schema_readiness import check_configured_database_schema_readiness
from app.services.sessions import cleanup_expired_sessions


def run_session_cleanup() -> int:
    with SessionLocal() as db:
        deleted = cleanup_expired_sessions(db)
        db.commit()
    print(json.dumps({"deleted_sessions": deleted}, sort_keys=True))
    return 0


def run_schema_status() -> int:
    result = check_configured_database_schema_readiness()
    print(json.dumps(result.to_public_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "ready" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASTRA bounded maintenance commands")
    commands = parser.add_subparsers(dest="command", required=True)

    cleanup = commands.add_parser("session-cleanup", help="Delete revoked sessions whose expiry is in the past")
    cleanup.set_defaults(handler=run_session_cleanup)

    schema = commands.add_parser("schema-status", help="Report database and Alembic schema readiness")
    schema.set_defaults(handler=run_schema_status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler())


if __name__ == "__main__":
    raise SystemExit(main())
