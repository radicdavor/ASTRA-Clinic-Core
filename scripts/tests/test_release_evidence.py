from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.release_evidence import (
    EXPECTED_MIGRATION_HEAD,
    ReleaseEvidenceError,
    _canonical_json,
    _sha256_bytes,
    documentation_truth_report,
    produce_release_manifest,
    validate_release_manifest,
)
from scripts.validate_pr3_remediation_closure import (
    DEFAULT_CONTRACT,
    produce_evidence,
)


SOURCE_SHA = "a" * 40
OTHER_SHA = "b" * 40
RUN_ID = "123456"


def build_behaviour_evidence(tmp_path: Path) -> tuple[Path, datetime]:
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    evidence_dir = tmp_path / "execution"
    now = datetime.now(timezone.utc).replace(microsecond=0)
    for index, (unit_id, unit) in enumerate(contract["behaviour_units"].items()):
        unit_dir = evidence_dir / unit_id
        unit_dir.mkdir(parents=True)
        output = unit_dir / f"{unit_id}.log"
        output.write_text("\n".join([*unit["test_ids"], "1 passed"]) + "\n", encoding="utf-8")
        produce_evidence(
            contract_path=DEFAULT_CONTRACT,
            unit_id=unit_id,
            source_sha=SOURCE_SHA,
            workflow_run_id=RUN_ID,
            job_name=f"job-{index}",
            test_command=f"command-{index}",
            output_log=output,
            evidence_file=unit_dir / f"{unit_id}.json",
            started_at=(now - timedelta(minutes=1)).isoformat(),
            completed_at=now.isoformat(),
        )
    return evidence_dir, now


def build_manifest(tmp_path: Path) -> tuple[Path, datetime]:
    evidence_dir, now = build_behaviour_evidence(tmp_path)
    manifest = tmp_path / "release-evidence.json"
    produce_release_manifest(
        evidence_dir=evidence_dir,
        source_sha=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        workflow_name="CI",
        workflow_event="pull_request",
        producer_results={"backend": "success", "frontend": "success", "e2e-db": "success"},
        output_path=manifest,
        generated_at=now.isoformat(),
    )
    return manifest, now


def rewrite_manifest(path: Path, mutation) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutation(payload)
    payload.pop("artifact_hash", None)
    payload["artifact_hash"] = _sha256_bytes(_canonical_json(payload))
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.with_suffix(path.suffix + ".sha256").write_text(
        hashlib.sha256(path.read_bytes()).hexdigest() + "\n", encoding="ascii"
    )


def validate(path: Path, now: datetime, *, source_sha: str = SOURCE_SHA):
    return validate_release_manifest(
        manifest_path=path,
        source_sha=source_sha,
        workflow_run_id=RUN_ID,
        now=now,
    )


def test_valid_exact_sha_release_evidence_passes(tmp_path):
    manifest, now = build_manifest(tmp_path)
    result = validate(manifest, now)
    assert result["source_sha"] == SOURCE_SHA
    assert result["behaviour_units"] == 5
    assert result["coverage_dimensions"] == 6
    assert result["migration_head"] == EXPECTED_MIGRATION_HEAD


def test_wrong_sha_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    with pytest.raises(ReleaseEvidenceError, match="another source SHA"):
        validate(manifest, now, source_sha=OTHER_SHA)


def test_failed_producer_is_rejected_before_manifest_creation(tmp_path):
    evidence_dir, now = build_behaviour_evidence(tmp_path)
    with pytest.raises(ReleaseEvidenceError, match="producer"):
        produce_release_manifest(
            evidence_dir=evidence_dir,
            source_sha=SOURCE_SHA,
            workflow_run_id=RUN_ID,
            workflow_name="CI",
            workflow_event="push",
            producer_results={"backend": "failure"},
            output_path=tmp_path / "release.json",
            generated_at=now.isoformat(),
        )


def test_stale_manifest_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    with pytest.raises(ReleaseEvidenceError, match="stale"):
        validate(manifest, now + timedelta(hours=25))


def test_internal_artifact_hash_mismatch_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["review"]["status"] = "approved"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest.with_suffix(manifest.suffix + ".sha256").write_text(
        hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n", encoding="ascii"
    )
    with pytest.raises(ReleaseEvidenceError, match="artifact hash"):
        validate(manifest, now)


def test_file_hash_sidecar_mismatch_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    manifest.with_suffix(manifest.suffix + ".sha256").write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(ReleaseEvidenceError, match="file hash"):
        validate(manifest, now)


def test_skipped_target_test_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["tests"].update(skipped_target_tests=1))
    with pytest.raises(ReleaseEvidenceError, match="skipped"):
        validate(manifest, now)


def test_migration_head_drift_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["migrations"].update(observed_head="0069_legacy_document_trust"))
    with pytest.raises(ReleaseEvidenceError, match="Alembic"):
        validate(manifest, now)


def test_false_formal_security_closure_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["security"].update(formal_codex_security_closure="approved", sealed=True))
    with pytest.raises(ReleaseEvidenceError, match="security limitation"):
        validate(manifest, now)


def test_unauthorized_production_claim_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["authorization"].update(production=True))
    with pytest.raises(ReleaseEvidenceError, match="unauthorized"):
        validate(manifest, now)


def test_readiness_layers_cannot_be_collapsed(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["readiness"].pop("real_patient_data"))
    with pytest.raises(ReleaseEvidenceError, match="not separated"):
        validate(manifest, now)


def test_document_truth_report_accepts_current_structured_claims(tmp_path):
    document = tmp_path / "release.md"
    document.write_text(
        f"CURRENT_HEAD: {SOURCE_SHA}\nALEMBIC_HEAD: {EXPECTED_MIGRATION_HEAD}\nUNRESOLVED_FINDINGS: 0\n",
        encoding="utf-8",
    )
    assert documentation_truth_report(
        documents=[document],
        source_sha=SOURCE_SHA,
        migration_head=EXPECTED_MIGRATION_HEAD,
        unresolved_findings=0,
    ) == {"documents": 1, "status": "pass"}


@pytest.mark.parametrize(
    "claim,error",
    [
        (f"CURRENT_HEAD: {OTHER_SHA}\n", "stale current HEAD"),
        ("ALEMBIC_HEAD: 0069_legacy_document_trust\n", "stale migration head"),
        ("FORMAL CODEX SECURITY CLOSURE: APPROVED\n", "false formal security closure"),
        ("UNRESOLVED_FINDINGS: 2\n", "stale unresolved finding count"),
    ],
)
def test_document_truth_report_rejects_stale_or_false_claims(tmp_path, claim, error):
    document = tmp_path / "release.md"
    document.write_text(claim, encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match=error):
        documentation_truth_report(
            documents=[document],
            source_sha=SOURCE_SHA,
            migration_head=EXPECTED_MIGRATION_HEAD,
            unresolved_findings=0,
        )
