from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from app.core.database import SessionLocal
from app.services.schema_readiness import check_configured_database_schema_readiness
from app.services.sessions import cleanup_expired_sessions


def run_session_cleanup(args: argparse.Namespace) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=args.retention_days)
    remaining = args.max_rows
    affected = 0
    with SessionLocal() as db:
        while remaining > 0:
            batch_limit = min(args.batch_size, remaining)
            batch = cleanup_expired_sessions(
                db,
                older_than=cutoff,
                max_rows=batch_limit,
                dry_run=args.dry_run,
            )
            affected += batch
            remaining -= batch
            if args.dry_run or batch < batch_limit:
                break
            db.commit()
        if not args.dry_run:
            db.commit()
    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "matched_sessions" if args.dry_run else "deleted_sessions": affected,
                "retention_days": args.retention_days,
            },
            sort_keys=True,
        )
    )
    return 0


def run_schema_status(_args: argparse.Namespace) -> int:
    result = check_configured_database_schema_readiness()
    print(json.dumps(result.to_public_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "ready" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASTRA bounded maintenance commands")
    commands = parser.add_subparsers(dest="command", required=True)

    cleanup = commands.add_parser("session-cleanup", help="Delete revoked sessions whose expiry is in the past")
    cleanup.add_argument("--dry-run", action="store_true", help="Count eligible rows without deleting them")
    cleanup.add_argument("--retention-days", type=_non_negative_int, default=0)
    cleanup.add_argument("--batch-size", type=_positive_int, default=1000)
    cleanup.add_argument("--max-rows", type=_positive_int, default=10000)
    cleanup.set_defaults(handler=run_session_cleanup)

    schema = commands.add_parser("schema-status", help="Report database and Alembic schema readiness")
    schema.set_defaults(handler=run_schema_status)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value < 1:
        raise argparse.ArgumentTypeError("vrijednost mora biti veća od nule")
    return value


def _non_negative_int(raw: str) -> int:
    value = int(raw)
    if value < 0:
        raise argparse.ArgumentTypeError("vrijednost ne smije biti negativna")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
