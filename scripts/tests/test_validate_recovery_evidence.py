from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from recovery_common import (  # noqa: E402
    FINAL_ALEMBIC_REVISION,
    RECOVERY_TEST_IDS,
    SUPPORTED_BACKUP_REVISIONS,
    RecoveryError,
    canonical_json_bytes,
    sha256_file,
)
from validate_recovery_evidence import (  # noqa: E402
    ALLOWED_FUTURE_CLOCK_SKEW,
    _record_hash,
    validate as validate_directory,
    validate_record,
)


SOURCE_SHA = "a" * 40
RUN_ID = "12345"
WORKFLOW_EVENT = "pull_request"
WORKFLOW_BRANCH = "fix/recovery-contract-0071"
NOW = datetime(2026, 7, 27, 16, 0, tzinfo=UTC)


def record() -> dict:
    scenarios = [
        {
            "source_revision": revision,
            "restored_revision": revision,
            "final_revision": FINAL_ALEMBIC_REVISION,
            "backup_hash": "b" * 64,
            "manifest_hash": "c" * 64,
            "semantic_checksum_count": 10,
            "membership_recovery": "passed",
            "document_provenance_recovery": "passed",
            "audit_recovery": "passed",
            "application_smoke": "passed",
            "cleanup_status": "completed",
        }
        for revision in sorted(SUPPORTED_BACKUP_REVISIONS)
    ]
    value = {
        "schema_version": 1,
        "source_sha": SOURCE_SHA,
        "expected_source_sha": SOURCE_SHA,
        "app_commit": SOURCE_SHA,
        "workflow_run_id": RUN_ID,
        "workflow_event": WORKFLOW_EVENT,
        "workflow_branch": WORKFLOW_BRANCH,
        "job_name": "recovery",
        "producer": "scripts/validate_recovery_evidence.py@1",
        "producer_status": "success",
        "execution_status": "completed",
        "conclusion": "success",
        "skipped_count": 0,
        "started_at": (NOW - timedelta(minutes=5)).isoformat(),
        "completed_at": NOW.isoformat(),
        "postgresql_version": "160014",
        "empty_database_final_revision": FINAL_ALEMBIC_REVISION,
        "scenarios": scenarios,
        "test_ids": list(RECOVERY_TEST_IDS),
        "cleanup_status": "completed",
        "scenario_result_file": "scenario-result.json",
        "scenario_result_hash": "e" * 64,
        "test_output_file": "recovery-integration.log",
        "test_output_hash": "d" * 64,
    }
    value["record_hash"] = _record_hash(value)
    return value


def validate(value: dict) -> dict:
    return validate_record(
        value,
        expected_source_sha=SOURCE_SHA,
        expected_declared_source_sha=SOURCE_SHA,
        expected_app_commit=SOURCE_SHA,
        expected_workflow_run_id=RUN_ID,
        expected_workflow_event=WORKFLOW_EVENT,
        expected_workflow_branch=WORKFLOW_BRANCH,
        max_age_hours=24,
        now=NOW,
    )


def rehash(value: dict) -> dict:
    value["record_hash"] = _record_hash(value)
    return value


def write_scenario_result(directory: Path, value: dict) -> Path:
    result = {
        "started_at": value["started_at"],
        "completed_at": value["completed_at"],
        "postgresql_version": value["postgresql_version"],
        "empty_database_final_revision": value["empty_database_final_revision"],
        "scenarios": deepcopy(value["scenarios"]),
        "test_ids": value["test_ids"],
        "cleanup_status": value["cleanup_status"],
    }
    path = directory / value["scenario_result_file"]
    path.write_bytes(canonical_json_bytes(result))
    value["scenario_result_hash"] = sha256_file(path)
    return path


def test_valid_exact_sha_evidence_passes():
    assert validate(record())["conclusion"] == "success"


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (lambda ids: [], "test_ids_mismatch"),
        (lambda ids: ids[:-1], "test_ids_mismatch"),
        (lambda ids: ids[:-2], "test_ids_mismatch"),
        (lambda ids: ids + ["unknown"], "test_ids_mismatch"),
        (lambda ids: ids + [ids[0]], "test_ids_duplicate"),
        (lambda ids: ["placeholder"], "test_ids_mismatch"),
        (lambda ids: "not-a-list", "test_ids_wrong_type"),
        (lambda ids: {"id": ids[0]}, "test_ids_wrong_type"),
        (lambda ids: None, "test_ids_wrong_type"),
        (lambda ids: 1, "test_ids_wrong_type"),
        (lambda ids: True, "test_ids_wrong_type"),
        (lambda ids: ids[:-1] + [1], "test_id_invalid"),
        (lambda ids: ids[:-1] + [""], "test_id_invalid"),
        (lambda ids: list(reversed(ids)), "test_ids_mismatch"),
    ],
)
def test_rehashed_noncanonical_test_ids_are_rejected(mutation, error):
    value = record()
    value["test_ids"] = mutation(list(RECOVERY_TEST_IDS))
    rehash(value)
    with pytest.raises(RecoveryError, match=error):
        validate(value)


def test_wrong_sha_fails():
    value = record()
    value["source_sha"] = "e" * 40
    with pytest.raises(RecoveryError, match="wrong_sha"):
        validate(value)


@pytest.mark.parametrize(
    "field",
    ["expected_source_sha", "app_commit"],
)
def test_divergent_declared_source_identity_fails(field):
    value = record()
    value[field] = "e" * 40
    rehash(value)
    with pytest.raises(RecoveryError, match="wrong_sha"):
        validate(value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workflow_event", "deployment"),
        ("workflow_branch", ""),
    ],
)
def test_wrong_workflow_identity_fails(field, value):
    record_value = record()
    record_value[field] = value
    rehash(record_value)
    with pytest.raises(RecoveryError, match="wrong_workflow"):
        validate(record_value)


def test_missing_source_sha_fails():
    value = record()
    del value["source_sha"]
    rehash(value)
    with pytest.raises(RecoveryError, match="invalid_recovery_evidence"):
        validate(value)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("production_authorized",), True),
        (("owner_rpo_rto_accepted",), True),
        (("readiness",), "ready"),
        (("scenarios", 0, "production_authorized"), True),
    ],
)
def test_unknown_security_significant_keys_fail(path, value):
    mutated = record()
    target = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    rehash(mutated)
    with pytest.raises(
        RecoveryError,
        match="invalid_recovery_evidence|invalid_recovery_evidence_scenario",
    ):
        validate(mutated)


def test_unknown_schema_version_fails():
    value = record()
    value["schema_version"] = 2
    rehash(value)
    with pytest.raises(RecoveryError, match="invalid_recovery_evidence"):
        validate(value)


def test_wrong_known_field_type_fails():
    value = record()
    value["skipped_count"] = "0"
    rehash(value)
    with pytest.raises(RecoveryError, match="invalid_recovery_evidence"):
        validate(value)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), True),
        (("skipped_count",), False),
        (("scenarios", 0, "semantic_checksum_count"), True),
    ],
)
def test_bool_is_not_accepted_as_integer(path, value):
    mutated = record()
    target = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    rehash(mutated)
    with pytest.raises(
        RecoveryError,
        match="invalid_recovery_evidence|missing_semantic_checksum",
    ):
        validate(mutated)


def test_wrong_run_fails():
    value = record()
    value["workflow_run_id"] = "999"
    with pytest.raises(RecoveryError, match="wrong_run"):
        validate(value)


def test_skipped_critical_test_fails():
    value = rehash({**record(), "skipped_count": 1})
    with pytest.raises(RecoveryError, match="skipped_test"):
        validate(value)


def test_failed_producer_fails():
    value = rehash({**record(), "producer_status": "failure"})
    with pytest.raises(RecoveryError, match="failed_producer"):
        validate(value)


def test_stale_evidence_fails():
    value = record()
    value["completed_at"] = (NOW - timedelta(hours=25)).isoformat()
    value["started_at"] = (NOW - timedelta(hours=26)).isoformat()
    rehash(value)
    with pytest.raises(RecoveryError, match="stale"):
        validate(value)


@pytest.mark.parametrize(
    "offset",
    [
        timedelta(0),
        ALLOWED_FUTURE_CLOCK_SKEW - timedelta(microseconds=1),
        ALLOWED_FUTURE_CLOCK_SKEW,
    ],
)
def test_completed_at_accepts_recent_and_bounded_future_clock_skew(offset):
    value = record()
    value["started_at"] = (NOW - timedelta(minutes=1)).isoformat()
    value["completed_at"] = (NOW + offset).isoformat()
    rehash(value)
    assert validate(value)["conclusion"] == "success"


@pytest.mark.parametrize(
    "offset",
    [
        ALLOWED_FUTURE_CLOCK_SKEW + timedelta(microseconds=1),
        timedelta(days=365),
    ],
)
def test_completed_at_rejects_timestamp_beyond_future_clock_skew(offset):
    value = record()
    value["completed_at"] = (NOW + offset).isoformat()
    rehash(value)
    with pytest.raises(RecoveryError, match="completed_at_in_future"):
        validate(value)


def test_completed_at_timezone_offset_normalizes_to_same_utc_instant():
    value = record()
    value["completed_at"] = NOW.astimezone(
        timezone(timedelta(hours=2))
    ).isoformat()
    rehash(value)
    assert validate(value)["conclusion"] == "success"


@pytest.mark.parametrize("timestamp", ["2026-07-30T18:00:00", "not-a-timestamp"])
def test_completed_at_rejects_naive_or_invalid_timestamp(timestamp):
    value = record()
    value["completed_at"] = timestamp
    rehash(value)
    with pytest.raises(RecoveryError, match="invalid_recovery_evidence_timestamp"):
        validate(value)


def test_invalid_record_hash_fails():
    value = record()
    value["record_hash"] = "0" * 64
    with pytest.raises(RecoveryError, match="hash_mismatch"):
        validate(value)


def test_missing_revision_scenario_fails():
    value = record()
    value["scenarios"].pop()
    rehash(value)
    with pytest.raises(RecoveryError, match="missing_revision"):
        validate(value)


def test_restored_revision_mismatch_fails():
    value = record()
    value["scenarios"][0]["restored_revision"] = FINAL_ALEMBIC_REVISION
    rehash(value)
    with pytest.raises(RecoveryError, match="missing_revision"):
        validate(value)


def test_missing_semantic_checksum_fails():
    value = record()
    value["scenarios"][0]["semantic_checksum_count"] = 0
    rehash(value)
    with pytest.raises(RecoveryError, match="missing_semantic_checksum"):
        validate(value)


def test_incomplete_cleanup_fails():
    value = rehash({**record(), "cleanup_status": "failed"})
    with pytest.raises(RecoveryError, match="incomplete_cleanup"):
        validate(value)


def test_scenario_cleanup_failure_fails():
    value = record()
    value["scenarios"][0]["cleanup_status"] = "failed"
    rehash(value)
    with pytest.raises(RecoveryError, match="incomplete_cleanup"):
        validate(value)


def test_duplicate_scenario_fails():
    value = record()
    value["scenarios"][1]["source_revision"] = value["scenarios"][0][
        "source_revision"
    ]
    rehash(value)
    with pytest.raises(RecoveryError, match="conflict"):
        validate(value)


def test_failed_security_semantics_fails():
    value = record()
    value["scenarios"][0]["membership_recovery"] = "failed"
    rehash(value)
    with pytest.raises(RecoveryError, match="failed_scenario"):
        validate(value)


def test_downloaded_output_log_hash_is_revalidated(tmp_path):
    evidence = tmp_path / "recovery-evidence.json"
    output = tmp_path / "recovery-integration.log"
    output.write_text("executed recovery matrix\n", encoding="utf-8")
    value = record()
    write_scenario_result(tmp_path, value)
    value["test_output_hash"] = sha256_file(output)
    rehash(value)
    evidence.write_bytes(canonical_json_bytes(value))
    args = argparse.Namespace(
        evidence_dir=tmp_path,
        source_sha=SOURCE_SHA,
        expected_source_sha=SOURCE_SHA,
        app_commit=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        workflow_event=WORKFLOW_EVENT,
        workflow_branch=WORKFLOW_BRANCH,
        max_age_hours=24,
    )
    validate_directory(args, now=NOW)
    output.write_text("tampered output\n", encoding="utf-8")
    with pytest.raises(RecoveryError, match="hash_mismatch"):
        validate_directory(args, now=NOW)


def test_rehashed_scenario_checksum_mutation_is_rejected_by_real_entrypoint(tmp_path):
    evidence = tmp_path / "recovery-evidence.json"
    output = tmp_path / "recovery-integration.log"
    output.write_text("executed recovery matrix\n", encoding="utf-8")
    value = record()
    write_scenario_result(tmp_path, value)
    value["test_output_hash"] = sha256_file(output)
    value["scenarios"][0]["backup_hash"] = "f" * 64
    rehash(value)
    evidence.write_bytes(canonical_json_bytes(value))
    args = argparse.Namespace(
        evidence_dir=tmp_path,
        source_sha=SOURCE_SHA,
        expected_source_sha=SOURCE_SHA,
        app_commit=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        workflow_event=WORKFLOW_EVENT,
        workflow_branch=WORKFLOW_BRANCH,
        max_age_hours=24,
    )
    with pytest.raises(RecoveryError, match="scenario_result_mismatch"):
        validate_directory(args, now=NOW)


def test_rehashed_future_completed_at_is_rejected_by_real_entrypoint(tmp_path):
    evidence = tmp_path / "recovery-evidence.json"
    output = tmp_path / "recovery-integration.log"
    output.write_text("executed recovery matrix\n", encoding="utf-8")
    value = record()
    value["completed_at"] = (NOW + timedelta(days=365)).isoformat()
    write_scenario_result(tmp_path, value)
    value["test_output_hash"] = sha256_file(output)
    rehash(value)
    evidence.write_bytes(canonical_json_bytes(value))
    args = argparse.Namespace(
        evidence_dir=tmp_path,
        source_sha=SOURCE_SHA,
        expected_source_sha=SOURCE_SHA,
        app_commit=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        workflow_event=WORKFLOW_EVENT,
        workflow_branch=WORKFLOW_BRANCH,
        max_age_hours=24,
    )
    with pytest.raises(RecoveryError, match="completed_at_in_future"):
        validate_directory(args, now=NOW)


def test_duplicate_json_key_is_rejected_by_real_entrypoint(tmp_path):
    evidence = tmp_path / "recovery-evidence.json"
    output = tmp_path / "recovery-integration.log"
    output.write_text("executed recovery matrix\n", encoding="utf-8")
    value = record()
    write_scenario_result(tmp_path, value)
    value["test_output_hash"] = sha256_file(output)
    rehash(value)
    serialized = canonical_json_bytes(value).decode("utf-8")
    serialized = serialized.replace(
        '"source_sha":"' + SOURCE_SHA + '"',
        '"source_sha":"' + SOURCE_SHA + '","source_sha":"' + SOURCE_SHA + '"',
        1,
    )
    evidence.write_text(serialized, encoding="utf-8")
    args = argparse.Namespace(
        evidence_dir=tmp_path,
        source_sha=SOURCE_SHA,
        expected_source_sha=SOURCE_SHA,
        app_commit=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        workflow_event=WORKFLOW_EVENT,
        workflow_branch=WORKFLOW_BRANCH,
        max_age_hours=24,
    )
    with pytest.raises(RecoveryError, match="duplicate_json_key"):
        validate_directory(args, now=NOW)
