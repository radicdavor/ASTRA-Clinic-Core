from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.validate_pr3_remediation_closure import validate_evidence
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from validate_pr3_remediation_closure import validate_evidence


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MIGRATION_HEAD = "0071_membership_taxonomy"
SCHEMA_VERSION = 1
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CANONICAL_PRODUCER_RESULTS = {
    "backend": "success",
    "frontend": "success",
    "e2e-db": "success",
}
CANONICAL_READINESS = {
    "code_merge": "evidence_complete_review_and_owner_decision_required",
    "deployment": "blocked",
    "production": "blocked",
    "real_patient_data": "blocked",
}
CURRENT_HEAD_PATTERN = re.compile(
    r"(?im)^\s*(?:CURRENT_HEAD|MAIN HEAD|PR #\d+ HEAD)\s*:\s*`?([0-9a-f]{40})`?\s*$"
)
MIGRATION_HEAD_PATTERN = re.compile(
    r"(?im)^\s*(?:ALEMBIC_HEAD|ALEMBIC HEAD|MIGRATION HEAD)\s*:\s*`?([0-9A-Za-z_]+)`?\s*$"
)
UNRESOLVED_PATTERN = re.compile(
    r"(?im)^\s*UNRESOLVED_FINDINGS\s*:\s*`?(\d+)`?\s*$"
)
FORMAL_CLOSURE_APPROVED_PATTERN = re.compile(
    r"(?im)FORMAL(?: CODEX)? SECURITY CLOSURE\s*:\s*APPROVED"
)
SECURITY_LIMITATION = "unavailable_due_to_platform_incident"


def _mapping(properties: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"kind": "mapping", "properties": properties}


def _string(
    *,
    enum: set[str] | None = None,
    pattern: re.Pattern[str] | None = None,
) -> dict[str, Any]:
    return {"kind": "string", "enum": enum, "pattern": pattern}


def _literal(value: Any) -> dict[str, Any]:
    return {"kind": "literal", "value": value}


CANONICAL_RELEASE_SCHEMA = _mapping(
    {
        "artifact_hash": _string(pattern=re.compile(r"^[0-9a-f]{64}$")),
        "authorization": _mapping(
            {
                "deployment": _literal(False),
                "merge": _literal(False),
                "production": _literal(False),
                "real_patient_data": _literal(False),
            }
        ),
        "ci": _mapping(
            {
                "event": _string(enum={"push", "pull_request"}),
                "execution_evidence": _literal("validated"),
                "producer_results": _mapping(
                    {
                        "backend": _literal("success"),
                        "e2e-db": _literal("success"),
                        "frontend": _literal("success"),
                    }
                ),
                "workflow_name": _literal("CI"),
                "workflow_run_id": _string(pattern=re.compile(r"^[1-9][0-9]*$")),
            }
        ),
        "credential_rotation": _mapping({"status": _literal("pending")}),
        "dependencies": _mapping({"issue_14": _literal("open")}),
        "deployment_validation": _mapping(
            {
                "proxy_topology": _literal("requires_validation"),
                "status": _literal("not_performed"),
            }
        ),
        "findings": _mapping(
            {
                "status": _string(enum={"not_supplied", "supplied"}),
                "unresolved_count": {
                    "kind": "nullable_integer",
                    "minimum": 0,
                },
            }
        ),
        "generated_at": _string(),
        "migrations": _mapping(
            {
                "expected_head": _literal(EXPECTED_MIGRATION_HEAD),
                "head_count": _literal(1),
                "observed_head": _literal(EXPECTED_MIGRATION_HEAD),
            }
        ),
        "producer": _mapping(
            {
                "name": _literal("scripts/release_evidence.py"),
                "version": _literal(1),
            }
        ),
        "readiness": _mapping(
            {key: _literal(value) for key, value in CANONICAL_READINESS.items()}
        ),
        "recovery": _mapping(
            {"status": _literal("not_evaluated_by_this_workflow")}
        ),
        "review": _mapping({"status": _literal("not_supplied")}),
        "schema_version": _literal(SCHEMA_VERSION),
        "security": _mapping(
            {
                "formal_codex_security_closure": _literal(SECURITY_LIMITATION),
                "manual_sealing_used": _literal(False),
                "sealed": _literal(False),
            }
        ),
        "source_sha": _string(pattern=SHA_PATTERN),
        "tests": _mapping(
            {
                "behaviour_units": _literal(5),
                "coverage_dimensions": _literal(6),
                "evidence_records": _literal(5),
                "executed_target_test_ids": _literal(16),
                "scope": _literal("remediation_execution_evidence"),
                "skipped_target_tests": _literal(0),
            }
        ),
        "usability": _mapping({"status": _literal("not_performed")}),
    }
)
CANONICAL_TOP_LEVEL_KEYS = frozenset(
    CANONICAL_RELEASE_SCHEMA["properties"]
)


class ReleaseEvidenceError(RuntimeError):
    pass


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseEvidenceError(
                f"Release evidence contains duplicate JSON key {key!r}"
            )
        result[key] = value
    return result


def _validate_schema_node(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    kind = schema["kind"]
    if kind == "mapping":
        if not isinstance(value, dict):
            raise ReleaseEvidenceError(
                f"{path}: expected mapping, got {type(value).__name__}"
            )
        properties = schema["properties"]
        actual_keys = set(value)
        expected_keys = set(properties)
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            unexpected = sorted(actual_keys - expected_keys)
            raise ReleaseEvidenceError(
                f"{path}: mapping keys must exactly match schema version 1; "
                f"missing={missing}, unexpected={unexpected}"
            )
        for key, child_schema in properties.items():
            _validate_schema_node(value[key], child_schema, f"{path}.{key}")
        return
    if kind == "string":
        if not isinstance(value, str):
            raise ReleaseEvidenceError(
                f"{path}: expected string, got {type(value).__name__}"
            )
        allowed = schema.get("enum")
        if allowed is not None and value not in allowed:
            raise ReleaseEvidenceError(
                f"{path}: value {value!r} is outside the closed domain"
            )
        pattern = schema.get("pattern")
        if pattern is not None and not pattern.fullmatch(value):
            raise ReleaseEvidenceError(
                f"{path}: value does not match the required format"
            )
        return
    if kind == "integer":
        if type(value) is not int:
            raise ReleaseEvidenceError(
                f"{path}: expected integer, got {type(value).__name__}"
            )
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise ReleaseEvidenceError(f"{path}: value must be at least {minimum}")
        return
    if kind == "nullable_integer":
        if value is None:
            return
        _validate_schema_node(
            value,
            {"kind": "integer", "minimum": schema.get("minimum")},
            path,
        )
        return
    if kind == "literal":
        expected = schema["value"]
        if type(value) is not type(expected) or value != expected:
            raise ReleaseEvidenceError(
                f"{path}: expected canonical value {expected!r}"
            )
        return
    if kind == "array":
        if not isinstance(value, list):
            raise ReleaseEvidenceError(
                f"{path}: expected array, got {type(value).__name__}"
            )
        for index, item in enumerate(value):
            _validate_schema_node(item, schema["items"], f"{path}[{index}]")
        return
    raise ReleaseEvidenceError(f"{path}: unsupported schema node {kind!r}")


def validate_checkout_identity(
    *,
    workflow_event: str,
    github_sha: str,
    pull_request_head_sha: str,
    checkout_sha: str,
) -> dict[str, str]:
    if workflow_event == "pull_request":
        expected_sha = pull_request_head_sha
        expected_field = "pull_request_head_sha"
    elif workflow_event == "push":
        expected_sha = github_sha
        expected_field = "github_sha"
    else:
        raise ReleaseEvidenceError(
            "Canonical release evidence supports only push and pull_request events"
        )
    if not SHA_PATTERN.fullmatch(expected_sha):
        raise ReleaseEvidenceError(
            f"{expected_field} must be a full lowercase Git SHA"
        )
    if not SHA_PATTERN.fullmatch(checkout_sha):
        raise ReleaseEvidenceError(
            "checkout_sha must be a full lowercase Git SHA"
        )
    if checkout_sha != expected_sha:
        raise ReleaseEvidenceError(
            "Checked-out revision does not match the event's canonical source SHA"
        )
    return {
        "workflow_event": workflow_event,
        "source_sha": checkout_sha,
    }


def _validate_producer_results(producer_results: Any) -> None:
    if not isinstance(producer_results, dict):
        raise ReleaseEvidenceError(
            "Producer results must be a mapping with the canonical producer set"
        )
    actual_names = set(producer_results)
    expected_names = set(CANONICAL_PRODUCER_RESULTS)
    if actual_names != expected_names:
        missing = sorted(expected_names - actual_names)
        unexpected = sorted(actual_names - expected_names)
        raise ReleaseEvidenceError(
            "Producer names must exactly match the canonical set; "
            f"missing={missing}, unexpected={unexpected}"
        )
    for name, expected_status in CANONICAL_PRODUCER_RESULTS.items():
        if producer_results.get(name) != expected_status:
            raise ReleaseEvidenceError(
                f"Canonical producer {name!r} must have status {expected_status!r}"
            )


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ReleaseEvidenceError(f"{field} is not a valid ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ReleaseEvidenceError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _literal_assignment(path: Path, name: str) -> str | tuple[str, ...] | None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        if value is None or isinstance(value, str):
            return value
        if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
            return value
        raise ReleaseEvidenceError(f"{path.name}: unsupported {name} declaration")
    raise ReleaseEvidenceError(f"{path.name}: missing {name} declaration")


def discover_migration_head(versions_dir: Path) -> str:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in sorted(versions_dir.glob("*.py")):
        revision = _literal_assignment(path, "revision")
        down_revision = _literal_assignment(path, "down_revision")
        if not isinstance(revision, str) or revision in revisions:
            raise ReleaseEvidenceError(f"{path.name}: invalid or duplicate revision")
        revisions.add(revision)
        if isinstance(down_revision, str):
            parents.add(down_revision)
        elif isinstance(down_revision, tuple):
            parents.update(down_revision)
    heads = revisions - parents
    if len(heads) != 1:
        raise ReleaseEvidenceError(f"Expected one Alembic head, found {sorted(heads)}")
    return next(iter(heads))


def _load_behaviour_records(evidence_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "behaviour_unit_id" in payload:
            records.append(payload)
    return records


def produce_release_manifest(
    *,
    evidence_dir: Path,
    source_sha: str,
    workflow_run_id: str,
    workflow_name: str,
    workflow_event: str,
    producer_results: dict[str, str],
    output_path: Path,
    generated_at: str,
    unresolved_findings: int | None = None,
    review_status: str = "not_supplied",
    recovery_status: str = "not_evaluated_by_this_workflow",
) -> dict[str, Any]:
    if not SHA_PATTERN.fullmatch(source_sha):
        raise ReleaseEvidenceError("source_sha must be a full lowercase Git SHA")
    if not workflow_run_id.strip() or not workflow_name.strip() or not workflow_event.strip():
        raise ReleaseEvidenceError("workflow identity is required")
    _validate_producer_results(producer_results)
    generated = _parse_timestamp(generated_at, "generated_at")
    behaviour_summary = validate_evidence(
        contract_path=ROOT / "docs" / "security" / "pr3-remediation-behavioural-review-units.json",
        evidence_dir=evidence_dir,
        source_sha=source_sha,
        workflow_run_id=workflow_run_id,
        now=generated,
    )
    records = _load_behaviour_records(evidence_dir)
    executed_test_ids = sum(len(record["test_ids"]) for record in records)
    skipped_target_tests = sum(int(record["skipped_count"]) for record in records)
    migration_head = discover_migration_head(ROOT / "backend" / "alembic" / "versions")
    if migration_head != EXPECTED_MIGRATION_HEAD:
        raise ReleaseEvidenceError(
            f"Observed Alembic head {migration_head!r} is not {EXPECTED_MIGRATION_HEAD!r}"
        )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_sha": source_sha,
        "generated_at": generated.isoformat(),
        "ci": {
            "workflow_name": workflow_name,
            "workflow_run_id": str(workflow_run_id),
            "event": workflow_event,
            "producer_results": dict(sorted(producer_results.items())),
            "execution_evidence": "validated",
        },
        "tests": {
            "scope": "remediation_execution_evidence",
            "behaviour_units": behaviour_summary["behaviour_units"],
            "coverage_dimensions": behaviour_summary["coverage_dimensions"],
            "evidence_records": behaviour_summary["execution_evidence_records"],
            "executed_target_test_ids": executed_test_ids,
            "skipped_target_tests": skipped_target_tests,
        },
        "migrations": {
            "expected_head": EXPECTED_MIGRATION_HEAD,
            "observed_head": migration_head,
            "head_count": 1,
        },
        "recovery": {"status": recovery_status},
        "findings": {
            "status": "supplied" if unresolved_findings is not None else "not_supplied",
            "unresolved_count": unresolved_findings,
        },
        "review": {"status": review_status},
        "security": {
            "formal_codex_security_closure": SECURITY_LIMITATION,
            "sealed": False,
            "manual_sealing_used": False,
        },
        "usability": {"status": "not_performed"},
        "credential_rotation": {"status": "pending"},
        "dependencies": {"issue_14": "open"},
        "deployment_validation": {
            "status": "not_performed",
            "proxy_topology": "requires_validation",
        },
        "authorization": {
            "merge": False,
            "deployment": False,
            "production": False,
            "real_patient_data": False,
        },
        "readiness": dict(CANONICAL_READINESS),
        "producer": {"name": "scripts/release_evidence.py", "version": 1},
    }
    payload["artifact_hash"] = _sha256_bytes(_canonical_json(payload))
    _validate_schema_node(payload, CANONICAL_RELEASE_SCHEMA)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output_path.with_suffix(output_path.suffix + ".sha256").write_text(
        _sha256_bytes(output_path.read_bytes()) + "\n", encoding="ascii"
    )
    return payload


def validate_release_manifest(
    *,
    manifest_path: Path,
    source_sha: str,
    workflow_run_id: str,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> dict[str, Any]:
    payload = json.loads(
        manifest_path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_object,
    )
    if not isinstance(payload, dict):
        raise ReleaseEvidenceError("Release evidence must be a JSON object")
    _validate_schema_node(payload, CANONICAL_RELEASE_SCHEMA)
    findings = payload["findings"]
    if (findings["status"] == "not_supplied") != (
        findings["unresolved_count"] is None
    ):
        raise ReleaseEvidenceError(
            "$.findings: status and unresolved_count are inconsistent"
        )
    if payload.get("source_sha") != source_sha:
        raise ReleaseEvidenceError("Release evidence belongs to another source SHA")
    if payload.get("ci", {}).get("workflow_run_id") != str(workflow_run_id):
        raise ReleaseEvidenceError("Release evidence belongs to another workflow run")
    generated = _parse_timestamp(payload.get("generated_at"), "generated_at")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if generated > current + timedelta(minutes=5) or current - generated > max_age:
        raise ReleaseEvidenceError("Release evidence is stale or from the future")
    artifact_hash = payload.get("artifact_hash")
    hash_input = dict(payload)
    hash_input.pop("artifact_hash", None)
    if artifact_hash != _sha256_bytes(_canonical_json(hash_input)):
        raise ReleaseEvidenceError("Release-evidence artifact hash mismatch")
    sidecar = manifest_path.with_suffix(manifest_path.suffix + ".sha256")
    if not sidecar.is_file() or sidecar.read_text(encoding="ascii").strip() != _sha256_bytes(
        manifest_path.read_bytes()
    ):
        raise ReleaseEvidenceError("Release-evidence file hash mismatch")
    ci = payload.get("ci", {})
    if ci.get("execution_evidence") != "validated":
        raise ReleaseEvidenceError("Execution evidence was not validated")
    _validate_producer_results(ci.get("producer_results"))
    tests = payload.get("tests", {})
    if tests.get("behaviour_units") != 5 or tests.get("coverage_dimensions") != 6:
        raise ReleaseEvidenceError("Release evidence lacks required behaviour coverage")
    if tests.get("skipped_target_tests") != 0:
        raise ReleaseEvidenceError("Release evidence contains skipped target tests")
    migrations = payload.get("migrations", {})
    if migrations != {
        "expected_head": EXPECTED_MIGRATION_HEAD,
        "observed_head": EXPECTED_MIGRATION_HEAD,
        "head_count": 1,
    }:
        raise ReleaseEvidenceError("Alembic head evidence is invalid")
    security = payload.get("security", {})
    if security.get("formal_codex_security_closure") != SECURITY_LIMITATION:
        raise ReleaseEvidenceError("Formal security limitation is misstated")
    if security.get("sealed") is not False or security.get("manual_sealing_used") is not False:
        raise ReleaseEvidenceError("Release evidence falsely claims formal sealing")
    authorization = payload.get("authorization", {})
    if any(authorization.get(key) is not False for key in ("merge", "deployment", "production", "real_patient_data")):
        raise ReleaseEvidenceError("Release evidence contains an unauthorized readiness claim")
    readiness = payload.get("readiness", {})
    if readiness != CANONICAL_READINESS:
        raise ReleaseEvidenceError(
            "Readiness claims do not match the canonical evidence-only state"
        )
    return {
        "source_sha": source_sha,
        "workflow_run_id": str(workflow_run_id),
        "behaviour_units": 5,
        "coverage_dimensions": 6,
        "migration_head": EXPECTED_MIGRATION_HEAD,
        "authorization_boundaries": "validated",
    }


def documentation_truth_report(
    *,
    documents: list[Path],
    source_sha: str,
    migration_head: str,
    unresolved_findings: int | None,
) -> dict[str, Any]:
    failures: list[str] = []
    for path in documents:
        content = path.read_text(encoding="utf-8")
        for value in CURRENT_HEAD_PATTERN.findall(content):
            if value != source_sha:
                failures.append(f"{path}: stale current HEAD {value}")
        for value in MIGRATION_HEAD_PATTERN.findall(content):
            if value != migration_head:
                failures.append(f"{path}: stale migration head {value}")
        if FORMAL_CLOSURE_APPROVED_PATTERN.search(content):
            failures.append(f"{path}: false formal security closure claim")
        if unresolved_findings is not None:
            for value in UNRESOLVED_PATTERN.findall(content):
                if int(value) != unresolved_findings:
                    failures.append(f"{path}: stale unresolved finding count {value}")
    if failures:
        raise ReleaseEvidenceError("; ".join(failures))
    return {"documents": len(documents), "status": "pass"}


def _producer_results(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ReleaseEvidenceError("producer-result must use NAME=STATUS")
        name, status = value.split("=", 1)
        if not name or name in result:
            raise ReleaseEvidenceError("Producer names must be non-empty and unique")
        result[name] = status
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    produce = subparsers.add_parser("produce")
    produce.add_argument("--evidence-dir", type=Path, required=True)
    produce.add_argument("--source-sha", required=True)
    produce.add_argument("--workflow-run-id", required=True)
    produce.add_argument("--workflow-name", required=True)
    produce.add_argument("--workflow-event", required=True)
    produce.add_argument("--producer-result", action="append", default=[])
    produce.add_argument("--output", type=Path, required=True)
    produce.add_argument("--generated-at", required=True)
    produce.add_argument("--unresolved-findings", type=int)
    produce.add_argument("--review-status", default="not_supplied")
    produce.add_argument("--recovery-status", default="not_evaluated_by_this_workflow")
    validate = subparsers.add_parser("validate")
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--source-sha", required=True)
    validate.add_argument("--workflow-run-id", required=True)
    validate.add_argument("--max-age-hours", type=float, default=24.0)
    truth = subparsers.add_parser("truth-report")
    truth.add_argument("--document", type=Path, action="append", required=True)
    truth.add_argument("--source-sha", required=True)
    truth.add_argument("--migration-head", default=EXPECTED_MIGRATION_HEAD)
    truth.add_argument("--unresolved-findings", type=int)
    checkout = subparsers.add_parser("verify-checkout")
    checkout.add_argument("--workflow-event", required=True)
    checkout.add_argument("--github-sha", required=True)
    checkout.add_argument("--pull-request-head-sha", default="")
    checkout.add_argument("--checkout-sha", required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "produce":
        result = produce_release_manifest(
            evidence_dir=args.evidence_dir,
            source_sha=args.source_sha,
            workflow_run_id=args.workflow_run_id,
            workflow_name=args.workflow_name,
            workflow_event=args.workflow_event,
            producer_results=_producer_results(args.producer_result),
            output_path=args.output,
            generated_at=args.generated_at,
            unresolved_findings=args.unresolved_findings,
            review_status=args.review_status,
            recovery_status=args.recovery_status,
        )
    elif args.command == "validate":
        result = validate_release_manifest(
            manifest_path=args.manifest,
            source_sha=args.source_sha,
            workflow_run_id=args.workflow_run_id,
            max_age=timedelta(hours=args.max_age_hours),
        )
    elif args.command == "truth-report":
        result = documentation_truth_report(
            documents=args.document,
            source_sha=args.source_sha,
            migration_head=args.migration_head,
            unresolved_findings=args.unresolved_findings,
        )
    else:
        result = validate_checkout_identity(
            workflow_event=args.workflow_event,
            github_sha=args.github_sha,
            pull_request_head_sha=args.pull_request_head_sha,
            checkout_sha=args.checkout_sha,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
