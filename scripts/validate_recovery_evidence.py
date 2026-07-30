from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from recovery_common import (
    FINAL_ALEMBIC_REVISION,
    RECOVERY_EVIDENCE_SCHEMA_VERSION,
    SUPPORTED_BACKUP_REVISIONS,
    RecoveryError,
    canonical_json_bytes,
    read_json,
    sha256_file,
    write_json,
)


REQUIRED_SCENARIOS = SUPPORTED_BACKUP_REVISIONS


def _is_lower_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise RecoveryError("invalid_recovery_evidence_timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise RecoveryError("invalid_recovery_evidence_timestamp") from exc
    if parsed.tzinfo is None:
        raise RecoveryError("invalid_recovery_evidence_timestamp")
    return parsed.astimezone(UTC)


def _record_hash(record: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in record.items() if key != "record_hash"}
    return sha256(canonical_json_bytes(unsigned)).hexdigest()


def produce(args: argparse.Namespace) -> dict[str, Any]:
    result = read_json(args.scenario_result)
    required_result = {
        "started_at",
        "completed_at",
        "postgresql_version",
        "empty_database_final_revision",
        "scenarios",
        "test_ids",
        "cleanup_status",
    }
    if not isinstance(result, dict) or set(result) != required_result:
        raise RecoveryError("invalid_recovery_scenario_result")
    record = {
        "schema_version": RECOVERY_EVIDENCE_SCHEMA_VERSION,
        "source_sha": args.source_sha,
        "expected_source_sha": args.expected_source_sha,
        "app_commit": args.app_commit,
        "workflow_run_id": str(args.workflow_run_id),
        "workflow_event": args.workflow_event,
        "workflow_branch": args.workflow_branch,
        "job_name": args.job_name,
        "producer": "scripts/validate_recovery_evidence.py@1",
        "producer_status": "success",
        "execution_status": "completed",
        "conclusion": "success",
        "skipped_count": 0,
        "started_at": result["started_at"],
        "completed_at": result["completed_at"],
        "postgresql_version": result["postgresql_version"],
        "empty_database_final_revision": result["empty_database_final_revision"],
        "scenarios": result["scenarios"],
        "test_ids": result["test_ids"],
        "cleanup_status": result["cleanup_status"],
        "test_output_file": args.output_log.name,
        "test_output_hash": sha256_file(args.output_log),
    }
    record["record_hash"] = _record_hash(record)
    validate_record(
        record,
        expected_source_sha=args.source_sha,
        expected_declared_source_sha=args.expected_source_sha,
        expected_app_commit=args.app_commit,
        expected_workflow_run_id=str(args.workflow_run_id),
        expected_workflow_event=args.workflow_event,
        expected_workflow_branch=args.workflow_branch,
        max_age_hours=args.max_age_hours,
    )
    write_json(args.evidence_file, record)
    print(json.dumps({"recovery_scenarios": len(record["scenarios"]), "status": "success"}, sort_keys=True))
    return record


def validate_record(
    record: Any,
    *,
    expected_source_sha: str,
    expected_declared_source_sha: str,
    expected_app_commit: str,
    expected_workflow_run_id: str,
    expected_workflow_event: str,
    expected_workflow_branch: str,
    max_age_hours: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "schema_version",
        "source_sha",
        "expected_source_sha",
        "app_commit",
        "workflow_run_id",
        "workflow_event",
        "workflow_branch",
        "job_name",
        "producer",
        "producer_status",
        "execution_status",
        "conclusion",
        "skipped_count",
        "started_at",
        "completed_at",
        "postgresql_version",
        "empty_database_final_revision",
        "scenarios",
        "test_ids",
        "cleanup_status",
        "test_output_file",
        "test_output_hash",
        "record_hash",
    }
    if not isinstance(record, dict) or set(record) != required:
        raise RecoveryError("invalid_recovery_evidence")
    if (
        type(record["schema_version"]) is not int
        or record["schema_version"] != RECOVERY_EVIDENCE_SCHEMA_VERSION
        or not _is_lower_hex(record["source_sha"], 40)
        or not _is_lower_hex(record["expected_source_sha"], 40)
        or not _is_lower_hex(record["app_commit"], 40)
        or not isinstance(record["workflow_run_id"], str)
        or not record["workflow_run_id"].isdigit()
        or record["job_name"] != "recovery"
        or record["producer"] != "scripts/validate_recovery_evidence.py@1"
        or type(record["skipped_count"]) is not int
    ):
        raise RecoveryError("invalid_recovery_evidence")
    if record["source_sha"] != expected_source_sha:
        raise RecoveryError("recovery_evidence_wrong_sha")
    if (
        record["expected_source_sha"] != expected_declared_source_sha
        or record["source_sha"] != record["expected_source_sha"]
        or record["app_commit"] != expected_app_commit
        or record["app_commit"] != record["source_sha"]
    ):
        raise RecoveryError("recovery_evidence_wrong_sha")
    if str(record["workflow_run_id"]) != str(expected_workflow_run_id):
        raise RecoveryError("recovery_evidence_wrong_run")
    if (
        record["workflow_event"] != expected_workflow_event
        or record["workflow_event"]
        not in {"push", "pull_request", "workflow_dispatch"}
        or record["workflow_branch"] != expected_workflow_branch
        or not isinstance(record["workflow_branch"], str)
        or not record["workflow_branch"]
    ):
        raise RecoveryError("recovery_evidence_wrong_workflow")
    if (
        record["producer_status"] != "success"
        or record["execution_status"] != "completed"
        or record["conclusion"] != "success"
    ):
        raise RecoveryError("recovery_evidence_failed_producer")
    if record["skipped_count"] != 0:
        raise RecoveryError("recovery_evidence_skipped_test")
    if record["cleanup_status"] != "completed":
        raise RecoveryError("recovery_evidence_incomplete_cleanup")
    if record["empty_database_final_revision"] != FINAL_ALEMBIC_REVISION:
        raise RecoveryError("recovery_evidence_missing_revision")
    if not isinstance(record["test_ids"], list) or not record["test_ids"]:
        raise RecoveryError("recovery_evidence_missing_test_ids")
    for key in ("test_output_hash", "record_hash"):
        if not isinstance(record[key], str) or len(record[key]) != 64:
            raise RecoveryError("recovery_evidence_hash_mismatch")
    if (
        not isinstance(record["test_output_file"], str)
        or Path(record["test_output_file"]).name != record["test_output_file"]
        or record["test_output_file"] in {"", ".", ".."}
    ):
        raise RecoveryError("invalid_recovery_evidence")
    if record["record_hash"] != _record_hash(record):
        raise RecoveryError("recovery_evidence_hash_mismatch")
    started = _parse_timestamp(record["started_at"])
    completed = _parse_timestamp(record["completed_at"])
    current = now or datetime.now(UTC)
    if completed < started or current - completed > timedelta(hours=max_age_hours):
        raise RecoveryError("recovery_evidence_stale")
    scenarios = record["scenarios"]
    if not isinstance(scenarios, list):
        raise RecoveryError("invalid_recovery_evidence")
    revisions: set[str] = set()
    for scenario in scenarios:
        required_scenario = {
            "source_revision",
            "restored_revision",
            "final_revision",
            "backup_hash",
            "manifest_hash",
            "semantic_checksum_count",
            "membership_recovery",
            "document_provenance_recovery",
            "audit_recovery",
            "application_smoke",
            "cleanup_status",
        }
        if not isinstance(scenario, dict) or set(scenario) != required_scenario:
            raise RecoveryError("invalid_recovery_evidence_scenario")
        source = scenario["source_revision"]
        if source in revisions:
            raise RecoveryError("recovery_evidence_conflict")
        revisions.add(source)
        if (
            source not in REQUIRED_SCENARIOS
            or scenario["restored_revision"] != source
            or scenario["final_revision"] != FINAL_ALEMBIC_REVISION
        ):
            raise RecoveryError("recovery_evidence_missing_revision")
        if any(
            not _is_lower_hex(scenario[key], 64)
            for key in ("backup_hash", "manifest_hash")
        ):
            raise RecoveryError("recovery_evidence_hash_mismatch")
        if (
            type(scenario["semantic_checksum_count"]) is not int
            or scenario["semantic_checksum_count"] < 1
        ):
            raise RecoveryError("recovery_evidence_missing_semantic_checksum")
        for key in (
            "membership_recovery",
            "document_provenance_recovery",
            "audit_recovery",
            "application_smoke",
        ):
            if scenario[key] != "passed":
                raise RecoveryError("recovery_evidence_failed_scenario")
        if scenario["cleanup_status"] != "completed":
            raise RecoveryError("recovery_evidence_incomplete_cleanup")
    if revisions != REQUIRED_SCENARIOS:
        raise RecoveryError("recovery_evidence_missing_revision")
    return record


def validate(
    args: argparse.Namespace, *, now: datetime | None = None
) -> dict[str, int]:
    records = list(args.evidence_dir.rglob("recovery-evidence.json"))
    if len(records) != 1:
        raise RecoveryError("recovery_evidence_duplicate_or_missing")
    record = read_json(records[0])
    validate_record(
        record,
        expected_source_sha=args.source_sha,
        expected_declared_source_sha=args.expected_source_sha,
        expected_app_commit=args.app_commit,
        expected_workflow_run_id=str(args.workflow_run_id),
        expected_workflow_event=args.workflow_event,
        expected_workflow_branch=args.workflow_branch,
        max_age_hours=args.max_age_hours,
        now=now,
    )
    output_log = records[0].parent / record["test_output_file"]
    if not output_log.is_file() or sha256_file(output_log) != record["test_output_hash"]:
        raise RecoveryError("recovery_evidence_hash_mismatch")
    result = {
        "recovery_evidence_records": 1,
        "recovery_scenarios": len(record["scenarios"]),
    }
    print(json.dumps(result, sort_keys=True))
    return result


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    produce_parser = commands.add_parser("produce")
    produce_parser.add_argument("--scenario-result", type=Path, required=True)
    produce_parser.add_argument("--output-log", type=Path, required=True)
    produce_parser.add_argument("--evidence-file", type=Path, required=True)
    produce_parser.add_argument("--source-sha", required=True)
    produce_parser.add_argument("--expected-source-sha", required=True)
    produce_parser.add_argument("--app-commit", required=True)
    produce_parser.add_argument("--workflow-run-id", required=True)
    produce_parser.add_argument("--workflow-event", required=True)
    produce_parser.add_argument("--workflow-branch", required=True)
    produce_parser.add_argument("--job-name", required=True)
    produce_parser.add_argument("--max-age-hours", type=int, default=24)
    produce_parser.set_defaults(handler=produce)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--evidence-dir", type=Path, required=True)
    validate_parser.add_argument("--source-sha", required=True)
    validate_parser.add_argument("--expected-source-sha", required=True)
    validate_parser.add_argument("--app-commit", required=True)
    validate_parser.add_argument("--workflow-run-id", required=True)
    validate_parser.add_argument("--workflow-event", required=True)
    validate_parser.add_argument("--workflow-branch", required=True)
    validate_parser.add_argument("--max-age-hours", type=int, default=24)
    validate_parser.set_defaults(handler=validate)
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        args.handler(args)
        return 0
    except RecoveryError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
