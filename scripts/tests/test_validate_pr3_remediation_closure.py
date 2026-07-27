from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.validate_pr3_remediation_closure import (
    DEFAULT_CONTRACT,
    EvidenceValidationError,
    _canonical_json,
    _sha256_bytes,
    _sha256_file,
    produce_evidence,
    validate_evidence,
)


SOURCE_SHA = "a" * 40
OTHER_SHA = "b" * 40
RUN_ID = "123456"


def build_evidence_set(tmp_path: Path) -> tuple[Path, datetime]:
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    evidence_dir = tmp_path / "evidence"
    now = datetime.now(timezone.utc).replace(microsecond=0)
    for index, (unit_id, unit) in enumerate(contract["behaviour_units"].items()):
        unit_dir = evidence_dir / unit_id
        unit_dir.mkdir(parents=True)
        output = unit_dir / f"{unit_id}.log"
        output.write_text(
            "\n".join([*unit["test_ids"], "1 passed"]) + "\n",
            encoding="utf-8",
        )
        produce_evidence(
            contract_path=DEFAULT_CONTRACT,
            unit_id=unit_id,
            source_sha=SOURCE_SHA,
            workflow_run_id=RUN_ID,
            job_name=f"job-{index}",
            test_command=f"synthetic-command-{index}",
            output_log=output,
            evidence_file=unit_dir / f"{unit_id}.json",
            started_at=(now - timedelta(minutes=1)).isoformat(),
            completed_at=now.isoformat(),
        )
    return evidence_dir, now


def record_path(evidence_dir: Path, unit_id: str) -> Path:
    return evidence_dir / unit_id / f"{unit_id}.json"


def mutate_record(path: Path, mutation, *, rehash: bool = True) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutation(payload)
    if rehash:
        payload.pop("artifact_hash", None)
        payload["artifact_hash"] = _sha256_bytes(_canonical_json(payload))
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate(evidence_dir: Path, now: datetime, *, source_sha: str = SOURCE_SHA):
    return validate_evidence(
        contract_path=DEFAULT_CONTRACT,
        evidence_dir=evidence_dir,
        source_sha=source_sha,
        workflow_run_id=RUN_ID,
        now=now,
    )


def test_all_valid_actual_sha_execution_evidence_passes(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    assert validate(evidence_dir, now) == {
        "behaviour_units": 5,
        "coverage_dimensions": 6,
        "execution_evidence_records": 5,
    }


def test_wrong_source_sha_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    with pytest.raises(EvidenceValidationError, match="another source SHA"):
        validate(evidence_dir, now, source_sha=OTHER_SHA)


def test_skipped_targeted_test_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "context_initialization")
    mutate_record(path, lambda payload: payload.__setitem__("skipped_count", 1))
    with pytest.raises(EvidenceValidationError, match="skipped"):
        validate(evidence_dir, now)


def test_output_reported_skip_is_rejected_even_if_record_claims_zero(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "context_initialization")
    output = path.parent / "context_initialization.log"
    output.write_text(output.read_text(encoding="utf-8") + "1 skipped\n", encoding="utf-8")
    mutate_record(
        path,
        lambda payload: payload.__setitem__("test_output_hash", _sha256_file(output)),
    )
    with pytest.raises(EvidenceValidationError, match="output reports skipped"):
        validate(evidence_dir, now)


def test_failed_job_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "deployment_proxy_boundary")
    mutate_record(path, lambda payload: payload.__setitem__("conclusion", "failure"))
    with pytest.raises(EvidenceValidationError, match="did not succeed"):
        validate(evidence_dir, now)


def test_stale_artifact_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "cross_scope_dto_projection")
    stale = now - timedelta(days=2)

    def make_stale(payload):
        payload["started_at"] = (stale - timedelta(minutes=1)).isoformat()
        payload["completed_at"] = stale.isoformat()
        payload["freshness"]["generated_at"] = stale.isoformat()

    mutate_record(path, make_stale)
    with pytest.raises(EvidenceValidationError, match="stale"):
        validate(evidence_dir, now)


def test_invalid_evidence_artifact_hash_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "populated_legacy_upgrade")
    mutate_record(
        path,
        lambda payload: payload.__setitem__("job_name", "tampered"),
        rehash=False,
    )
    with pytest.raises(EvidenceValidationError, match="artifact hash mismatch"):
        validate(evidence_dir, now)


def test_invalid_test_output_hash_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    output = (
        evidence_dir
        / "transitional_workflow_rediscovery"
        / "transitional_workflow_rediscovery.log"
    )
    output.write_text("tampered output\n", encoding="utf-8")
    with pytest.raises(EvidenceValidationError, match="test output hash mismatch"):
        validate(evidence_dir, now)


def test_missing_behaviour_unit_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "context_initialization")
    path.unlink()
    with pytest.raises(EvidenceValidationError, match="Missing behaviour"):
        validate(evidence_dir, now)


def test_contract_dimension_without_executed_unit_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    for unit in contract["behaviour_units"].values():
        unit["coverage_dimensions"] = [
            dimension
            for dimension in unit["coverage_dimensions"]
            if dimension != "deployment_topology"
        ]
    bad_contract = tmp_path / "bad-contract.json"
    bad_contract.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(EvidenceValidationError, match="no behaviour unit"):
        validate_evidence(
            contract_path=bad_contract,
            evidence_dir=evidence_dir,
            source_sha=SOURCE_SHA,
            workflow_run_id=RUN_ID,
            now=now,
        )


def test_literal_selector_without_execution_record_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "populated_legacy_upgrade")
    path.write_text(
        json.dumps(
            {
                "behaviour_unit_id": "populated_legacy_upgrade",
                "selector": "def check_multi",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(EvidenceValidationError, match="missing execution fields"):
        validate(evidence_dir, now)


def test_valid_non_skipped_output_is_accepted_by_producer(tmp_path):
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    unit = contract["behaviour_units"]["deployment_proxy_boundary"]
    output = tmp_path / "proxy.log"
    output.write_text("\n".join([*unit["test_ids"], "3 passed"]) + "\n", encoding="utf-8")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    record = produce_evidence(
        contract_path=DEFAULT_CONTRACT,
        unit_id="deployment_proxy_boundary",
        source_sha=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        job_name="backend",
        test_command="pytest proxy",
        output_log=output,
        evidence_file=tmp_path / "proxy.json",
        started_at=(now - timedelta(seconds=2)).isoformat(),
        completed_at=now.isoformat(),
    )
    assert record["skipped_count"] == 0
    assert record["conclusion"] == "success"


def test_wrong_test_id_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    path = record_path(evidence_dir, "cross_scope_dto_projection")
    mutate_record(
        path,
        lambda payload: payload["test_ids"].__setitem__(0, "wrong-test-id"),
    )
    with pytest.raises(EvidenceValidationError, match="test IDs do not match"):
        validate(evidence_dir, now)


def test_duplicate_conflicting_evidence_is_rejected(tmp_path):
    evidence_dir, now = build_evidence_set(tmp_path)
    original = record_path(evidence_dir, "context_initialization")
    duplicate_dir = evidence_dir / "duplicate"
    duplicate_dir.mkdir()
    duplicate = duplicate_dir / "duplicate.json"
    duplicate.write_bytes(original.read_bytes())
    (duplicate_dir / "context_initialization.log").write_bytes(
        (original.parent / "context_initialization.log").read_bytes()
    )
    with pytest.raises(EvidenceValidationError, match="Duplicate/conflicting"):
        validate(evidence_dir, now)
