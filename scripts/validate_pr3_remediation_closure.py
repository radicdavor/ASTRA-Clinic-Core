from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "docs" / "security" / "pr3-remediation-behavioural-review-units.json"
)
EVIDENCE_SCHEMA_VERSION = 1
PRODUCER = {
    "name": "scripts/validate_pr3_remediation_closure.py",
    "version": 1,
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SKIP_PATTERNS = (
    re.compile(r"\b(\d+)\s+skipped\b", re.IGNORECASE),
    re.compile(r"\b(\d+)\s+skip(?:ped)?\b", re.IGNORECASE),
)


class EvidenceValidationError(RuntimeError):
    pass


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{field} is not a valid ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceValidationError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _skip_count(output: str) -> int:
    counts = [
        int(match.group(1))
        for pattern in SKIP_PATTERNS
        for match in pattern.finditer(output)
    ]
    return max(counts, default=0)


def _load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise EvidenceValidationError("Evidence contract schema_version must be 2")
    units = payload.get("behaviour_units")
    dimensions = payload.get("coverage_dimensions")
    if not isinstance(units, dict) or not units:
        raise EvidenceValidationError("Evidence contract has no behaviour_units")
    if not isinstance(dimensions, list) or not dimensions:
        raise EvidenceValidationError("Evidence contract has no coverage_dimensions")
    if len(dimensions) != len(set(dimensions)):
        raise EvidenceValidationError("Evidence contract contains duplicate coverage dimensions")
    for unit_id, unit in units.items():
        required = {
            "expected_failure_path",
            "test_ids",
            "environment",
            "coverage_dimensions",
        }
        missing = required - unit.keys()
        if missing:
            raise EvidenceValidationError(
                f"Contract unit {unit_id} is missing fields: {sorted(missing)}"
            )
        if not unit["test_ids"]:
            raise EvidenceValidationError(f"Contract unit {unit_id} has no test IDs")
        unknown = set(unit["coverage_dimensions"]) - set(dimensions)
        if unknown:
            raise EvidenceValidationError(
                f"Contract unit {unit_id} references unknown dimensions: {sorted(unknown)}"
            )
    covered = {
        dimension
        for unit in units.values()
        for dimension in unit["coverage_dimensions"]
    }
    missing_dimensions = set(dimensions) - covered
    if missing_dimensions:
        raise EvidenceValidationError(
            f"Contract dimensions have no behaviour unit: {sorted(missing_dimensions)}"
        )
    return payload


def produce_evidence(
    *,
    contract_path: Path,
    unit_id: str,
    source_sha: str,
    workflow_run_id: str,
    job_name: str,
    test_command: str,
    output_log: Path,
    evidence_file: Path,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    contract = _load_contract(contract_path)
    unit = contract["behaviour_units"].get(unit_id)
    if unit is None:
        raise EvidenceValidationError(f"Unknown behaviour unit: {unit_id}")
    if not SHA_PATTERN.fullmatch(source_sha):
        raise EvidenceValidationError("source_sha must be a full lowercase Git SHA")
    if not workflow_run_id.strip() or not job_name.strip() or not test_command.strip():
        raise EvidenceValidationError(
            "workflow_run_id, job_name, and test_command are required"
        )
    output = output_log.read_text(encoding="utf-8", errors="replace")
    missing_test_ids = [
        test_id for test_id in unit["test_ids"] if test_id not in output
    ]
    if missing_test_ids:
        raise EvidenceValidationError(
            f"Executed output does not contain required test IDs: {missing_test_ids}"
        )
    skipped_count = _skip_count(output)
    if skipped_count:
        raise EvidenceValidationError(
            f"Targeted evidence output contains {skipped_count} skipped tests"
        )
    started = _parse_timestamp(started_at, "started_at")
    completed = _parse_timestamp(completed_at, "completed_at")
    if completed < started:
        raise EvidenceValidationError("completed_at precedes started_at")
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    relative_output = Path(output_log.name)
    target_output = evidence_file.parent / relative_output
    if output_log.resolve() != target_output.resolve():
        target_output.write_bytes(output_log.read_bytes())
    payload: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "behaviour_unit_id": unit_id,
        "source_sha": source_sha,
        "workflow_run_id": str(workflow_run_id),
        "job_name": job_name,
        "test_command": test_command,
        "test_ids": unit["test_ids"],
        "execution_status": "completed",
        "conclusion": "success",
        "skipped_count": 0,
        "started_at": started.isoformat(),
        "completed_at": completed.isoformat(),
        "test_output_file": relative_output.as_posix(),
        "test_output_hash": _sha256_file(target_output),
        "expected_failure_path": unit["expected_failure_path"],
        "environment": unit["environment"],
        "coverage_dimensions": unit["coverage_dimensions"],
        "freshness": {
            "source_sha": source_sha,
            "generated_at": completed.isoformat(),
        },
        "producer": PRODUCER,
    }
    payload["artifact_hash"] = _sha256_bytes(_canonical_json(payload))
    evidence_file.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _safe_output_path(record_path: Path, relative_value: str) -> Path:
    relative = Path(relative_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise EvidenceValidationError(
            f"{record_path.name}: test_output_file must be a safe relative path"
        )
    output = (record_path.parent / relative).resolve()
    parent = record_path.parent.resolve()
    if output.parent != parent:
        raise EvidenceValidationError(
            f"{record_path.name}: test output must remain beside its evidence record"
        )
    return output


def validate_evidence(
    *,
    contract_path: Path,
    evidence_dir: Path,
    source_sha: str,
    workflow_run_id: str,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> dict[str, int]:
    contract = _load_contract(contract_path)
    if not SHA_PATTERN.fullmatch(source_sha):
        raise EvidenceValidationError("Expected source SHA must be a full lowercase Git SHA")
    expected_units = set(contract["behaviour_units"])
    record_paths = sorted(evidence_dir.rglob("*.json"))
    if not record_paths:
        raise EvidenceValidationError("No execution evidence records were found")
    records: dict[str, tuple[Path, dict[str, Any]]] = {}
    current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    covered_dimensions: set[str] = set()

    for record_path in record_paths:
        record = json.loads(record_path.read_text(encoding="utf-8"))
        unit_id = record.get("behaviour_unit_id")
        if unit_id not in expected_units:
            raise EvidenceValidationError(
                f"{record_path.name}: unknown behaviour unit {unit_id!r}"
            )
        if unit_id in records:
            raise EvidenceValidationError(
                f"Duplicate/conflicting execution evidence for {unit_id}"
            )
        required_fields = {
            "schema_version",
            "source_sha",
            "workflow_run_id",
            "job_name",
            "test_command",
            "test_ids",
            "execution_status",
            "conclusion",
            "skipped_count",
            "started_at",
            "completed_at",
            "test_output_file",
            "test_output_hash",
            "expected_failure_path",
            "environment",
            "coverage_dimensions",
            "freshness",
            "producer",
            "artifact_hash",
        }
        missing_fields = required_fields - record.keys()
        if missing_fields:
            raise EvidenceValidationError(
                f"{record_path.name}: missing execution fields {sorted(missing_fields)}"
            )
        if record["schema_version"] != EVIDENCE_SCHEMA_VERSION:
            raise EvidenceValidationError(
                f"{record_path.name}: unsupported evidence schema"
            )
        if record["source_sha"] != source_sha:
            raise EvidenceValidationError(
                f"{record_path.name}: evidence belongs to another source SHA"
            )
        if str(record["workflow_run_id"]) != str(workflow_run_id):
            raise EvidenceValidationError(
                f"{record_path.name}: evidence belongs to another workflow run"
            )
        if record["execution_status"] != "completed":
            raise EvidenceValidationError(f"{record_path.name}: job is not completed")
        if record["conclusion"] != "success":
            raise EvidenceValidationError(f"{record_path.name}: job did not succeed")
        if record["skipped_count"] != 0:
            raise EvidenceValidationError(
                f"{record_path.name}: targeted evidence contains skipped tests"
            )
        if not record["job_name"] or not record["test_command"]:
            raise EvidenceValidationError(
                f"{record_path.name}: job name and command are required"
            )

        unit_contract = contract["behaviour_units"][unit_id]
        if record["test_ids"] != unit_contract["test_ids"]:
            raise EvidenceValidationError(
                f"{record_path.name}: executed test IDs do not match the contract"
            )
        if record["expected_failure_path"] != unit_contract["expected_failure_path"]:
            raise EvidenceValidationError(
                f"{record_path.name}: expected failure path does not match the contract"
            )
        if set(record["environment"]) != set(unit_contract["environment"]):
            raise EvidenceValidationError(
                f"{record_path.name}: execution environment does not match the contract"
            )
        if set(record["coverage_dimensions"]) != set(
            unit_contract["coverage_dimensions"]
        ):
            raise EvidenceValidationError(
                f"{record_path.name}: coverage dimensions do not match the contract"
            )

        started = _parse_timestamp(record["started_at"], "started_at")
        completed = _parse_timestamp(record["completed_at"], "completed_at")
        if completed < started:
            raise EvidenceValidationError(
                f"{record_path.name}: completed_at precedes started_at"
            )
        if completed > current_time + timedelta(minutes=5):
            raise EvidenceValidationError(
                f"{record_path.name}: completion timestamp is in the future"
            )
        if current_time - completed > max_age:
            raise EvidenceValidationError(
                f"{record_path.name}: evidence is stale"
            )
        freshness = record["freshness"]
        if freshness != {
            "source_sha": source_sha,
            "generated_at": completed.isoformat(),
        }:
            raise EvidenceValidationError(
                f"{record_path.name}: freshness metadata is invalid"
            )
        if record["producer"] != PRODUCER:
            raise EvidenceValidationError(
                f"{record_path.name}: evidence producer is not trusted"
            )

        output_path = _safe_output_path(record_path, record["test_output_file"])
        if not output_path.is_file():
            raise EvidenceValidationError(
                f"{record_path.name}: test output artifact is missing"
            )
        if _sha256_file(output_path) != record["test_output_hash"]:
            raise EvidenceValidationError(
                f"{record_path.name}: test output hash mismatch"
            )
        output = output_path.read_text(encoding="utf-8", errors="replace")
        if _skip_count(output) != 0:
            raise EvidenceValidationError(
                f"{record_path.name}: test output reports skipped tests"
            )
        missing_test_ids = [
            test_id for test_id in record["test_ids"] if test_id not in output
        ]
        if missing_test_ids:
            raise EvidenceValidationError(
                f"{record_path.name}: test output is missing IDs {missing_test_ids}"
            )

        artifact_hash = record["artifact_hash"]
        hash_input = dict(record)
        del hash_input["artifact_hash"]
        if artifact_hash != _sha256_bytes(_canonical_json(hash_input)):
            raise EvidenceValidationError(
                f"{record_path.name}: evidence artifact hash mismatch"
            )

        covered_dimensions.update(record["coverage_dimensions"])
        records[unit_id] = (record_path, record)

    missing_units = expected_units - records.keys()
    if missing_units:
        raise EvidenceValidationError(
            f"Missing behaviour execution evidence: {sorted(missing_units)}"
        )
    missing_dimensions = set(contract["coverage_dimensions"]) - covered_dimensions
    if missing_dimensions:
        raise EvidenceValidationError(
            f"Missing executed coverage dimensions: {sorted(missing_dimensions)}"
        )
    return {
        "behaviour_units": len(records),
        "coverage_dimensions": len(covered_dimensions),
        "execution_evidence_records": len(record_paths),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    produce = subparsers.add_parser("produce")
    produce.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    produce.add_argument("--unit", required=True)
    produce.add_argument("--source-sha", required=True)
    produce.add_argument("--workflow-run-id", required=True)
    produce.add_argument("--job-name", required=True)
    produce.add_argument("--test-command", required=True)
    produce.add_argument("--output-log", type=Path, required=True)
    produce.add_argument("--evidence-file", type=Path, required=True)
    produce.add_argument("--started-at", required=True)
    produce.add_argument("--completed-at", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    validate.add_argument("--evidence-dir", type=Path, required=True)
    validate.add_argument("--source-sha", required=True)
    validate.add_argument("--workflow-run-id", required=True)
    validate.add_argument("--max-age-hours", type=float, default=24.0)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "produce":
        result = produce_evidence(
            contract_path=args.contract,
            unit_id=args.unit,
            source_sha=args.source_sha,
            workflow_run_id=args.workflow_run_id,
            job_name=args.job_name,
            test_command=args.test_command,
            output_log=args.output_log,
            evidence_file=args.evidence_file,
            started_at=args.started_at,
            completed_at=args.completed_at,
        )
    else:
        result = validate_evidence(
            contract_path=args.contract,
            evidence_dir=args.evidence_dir,
            source_sha=args.source_sha,
            workflow_run_id=args.workflow_run_id,
            max_age=timedelta(hours=args.max_age_hours),
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
