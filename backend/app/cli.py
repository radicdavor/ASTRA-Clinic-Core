from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from app.core.database import SessionLocal
from app.services.schema_readiness import check_configured_database_schema_readiness
from app.services.clinic_membership_migration import (
    MembershipMigrationResolutionError,
    membership_migration_status,
    resolve_membership_migration_issue,
)
from app.services.sessions import cleanup_expired_sessions


def run_session_cleanup(_args: argparse.Namespace | None = None) -> int:
    with SessionLocal() as db:
        deleted = cleanup_expired_sessions(db)
        db.commit()
    print(json.dumps({"deleted_sessions": deleted}, sort_keys=True))
    return 0


def run_schema_status(_args: argparse.Namespace | None = None) -> int:
    result = check_configured_database_schema_readiness()
    print(json.dumps(result.to_public_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if result.status == "ready" else 1


def run_membership_migration_status(_args: argparse.Namespace | None = None) -> int:
    with SessionLocal() as db:
        result = membership_migration_status(db)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["pending"] == 0 else 2


def run_resolve_membership_migration(args: argparse.Namespace) -> int:
    try:
        with SessionLocal() as db:
            issue = resolve_membership_migration_issue(
                db,
                user_email=args.user_email,
                clinic_id=args.clinic_id,
                operator_email=args.operator_email,
                note=args.note,
            )
            db.commit()
            result = {
                "issue_id": issue.id,
                "user_id": issue.user_id,
                "clinic_id": issue.resolution_clinic_id,
                "status": issue.status,
            }
    except MembershipMigrationResolutionError as exc:
        print(json.dumps({"status": "rejected", "detail": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASTRA bounded maintenance commands")
    commands = parser.add_subparsers(dest="command", required=True)

    cleanup = commands.add_parser("session-cleanup", help="Delete revoked sessions whose expiry is in the past")
    cleanup.set_defaults(handler=run_session_cleanup)

    schema = commands.add_parser("schema-status", help="Report database and Alembic schema readiness")
    schema.set_defaults(handler=run_schema_status)
    membership_status = commands.add_parser(
        "clinic-membership-migration-status",
        help="List unresolved clinic-membership migration decisions",
    )
    membership_status.set_defaults(handler=run_membership_migration_status)
    resolve_membership = commands.add_parser(
        "resolve-clinic-membership",
        help="Resolve one ambiguous legacy user-to-clinic membership",
    )
    resolve_membership.add_argument("--user-email", required=True)
    resolve_membership.add_argument("--clinic-id", required=True, type=int)
    resolve_membership.add_argument("--operator-email", required=True)
    resolve_membership.add_argument("--note", required=True)
    resolve_membership.set_defaults(handler=run_resolve_membership_migration)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
