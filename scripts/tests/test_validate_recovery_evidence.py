from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from recovery_common import (  # noqa: E402
    FINAL_ALEMBIC_REVISION,
    SUPPORTED_BACKUP_REVISIONS,
    RecoveryError,
    canonical_json_bytes,
    sha256_file,
)
from validate_recovery_evidence import (  # noqa: E402
    _record_hash,
    validate as validate_directory,
    validate_record,
)


SOURCE_SHA = "a" * 40
RUN_ID = "12345"
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
        "workflow_run_id": RUN_ID,
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
        "test_ids": ["empty-to-0071", "0062-to-0071", "0071-restore"],
        "cleanup_status": "completed",
        "test_output_file": "recovery-integration.log",
        "test_output_hash": "d" * 64,
    }
    value["record_hash"] = _record_hash(value)
    return value


def validate(value: dict) -> dict:
    return validate_record(
        value,
        expected_source_sha=SOURCE_SHA,
        expected_workflow_run_id=RUN_ID,
        max_age_hours=24,
        now=NOW,
    )


def rehash(value: dict) -> dict:
    value["record_hash"] = _record_hash(value)
    return value


def test_valid_exact_sha_evidence_passes():
    assert validate(record())["conclusion"] == "success"


def test_wrong_sha_fails():
    value = record()
    value["source_sha"] = "e" * 40
    with pytest.raises(RecoveryError, match="wrong_sha"):
        validate(value)


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
    value["test_output_hash"] = sha256_file(output)
    rehash(value)
    evidence.write_bytes(canonical_json_bytes(value))
    args = argparse.Namespace(
        evidence_dir=tmp_path,
        source_sha=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        max_age_hours=24,
    )
    validate_directory(args)
    output.write_text("tampered output\n", encoding="utf-8")
    with pytest.raises(RecoveryError, match="hash_mismatch"):
        validate_directory(args)
