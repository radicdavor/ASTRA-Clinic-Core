from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.release_evidence import (
    CANONICAL_PRODUCER_RESULTS,
    CANONICAL_READINESS,
    CANONICAL_TOP_LEVEL_KEYS,
    EXPECTED_MIGRATION_HEAD,
    ReleaseEvidenceError,
    _canonical_json,
    _producer_results,
    _sha256_bytes,
    documentation_truth_report,
    produce_release_manifest,
    validate_checkout_identity,
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


def parse_workflow_steps(workflow: str) -> dict[str, list[dict[str, str]]]:
    """Parse the concrete job/step structure used by this repository workflow."""
    jobs: dict[str, list[dict[str, str]]] = {}
    current_job: str | None = None
    in_steps = False
    current_step: dict[str, str] | None = None
    step_lines: list[str] = []

    def finish_step() -> None:
        nonlocal current_step, step_lines
        if current_job is not None and current_step is not None:
            current_step["raw"] = "\n".join(step_lines)
            jobs[current_job].append(current_step)
        current_step = None
        step_lines = []

    for line in workflow.splitlines():
        job_match = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if job_match:
            finish_step()
            current_job = job_match.group(1)
            jobs[current_job] = []
            in_steps = False
            continue
        if current_job is None:
            continue
        if line == "    steps:":
            in_steps = True
            continue
        if not in_steps:
            continue
        if re.match(r"^  [A-Za-z0-9_-]+:\s*$", line):
            finish_step()
            current_job = None
            in_steps = False
            continue
        step_match = re.match(r"^      - (uses|name|run):\s*(.*)$", line)
        if step_match:
            finish_step()
            current_step = {step_match.group(1): step_match.group(2)}
            step_lines = [line]
            continue
        if current_step is None:
            continue
        step_lines.append(line)
        property_match = re.match(r"^        (uses|name|run):\s*(.*)$", line)
        if property_match:
            current_step[property_match.group(1)] = property_match.group(2)
    finish_step()
    return jobs


def assert_workflow_contract(workflow: str) -> None:
    jobs = parse_workflow_steps(workflow)
    expected_jobs = {"backend", "frontend", "e2e-db", "remediation-evidence"}
    assert expected_jobs <= set(jobs)
    checkout_ref = "ref: ${{ github.event.pull_request.head.sha || github.sha }}"

    for job_name in expected_jobs:
        steps = jobs[job_name]
        checkout_indexes = [
            index
            for index, step in enumerate(steps)
            if step.get("uses", "").startswith("actions/checkout@")
        ]
        verify_indexes = [
            index
            for index, step in enumerate(steps)
            if step.get("name") == "Verify exact source checkout"
        ]
        assert checkout_indexes == [0], job_name
        assert verify_indexes == [1], job_name
        checkout = steps[0]
        verify = steps[1]
        verify_run = "\n".join(
            line
            for line in verify["raw"].splitlines()
            if not line.lstrip().startswith("#")
        )
        assert checkout_ref in checkout["raw"], job_name
        assert "run" in verify, job_name
        assert "git rev-parse HEAD" in verify_run, job_name
        assert "${{ github.event.pull_request.head.sha || github.sha }}" in verify_run, job_name
        assert 'exit 1' in verify_run, job_name
        assert "REMEDIATION_CHECKOUT_SHA" in verify_run, job_name
        assert all(
            index > verify_indexes[0]
            for index, step in enumerate(steps)
            if step.get("uses", "").startswith(("actions/setup-", "actions/download-artifact@"))
        ), job_name
        upload_indexes = [
            index
            for index, step in enumerate(steps)
            if step.get("uses", "").startswith("actions/upload-artifact@")
        ]
        assert upload_indexes == [len(steps) - 1], job_name

    def assert_named_order(job_name: str, names: list[str]) -> None:
        actual_names = [step.get("name", "") for step in jobs[job_name]]
        indexes = [actual_names.index(name) for name in names]
        assert indexes == sorted(indexes), job_name

    assert_named_order(
        "backend",
        [
            "Run PR3 security regression gate",
            "Run fast backend feedback gate",
            "Run backend non-integration tests",
            "Run explicit PostgreSQL integration gate",
            "Validate synthetic test backup and restore",
            "Produce episode and proxy execution evidence",
            "Upload backend remediation evidence",
        ],
    )
    assert_named_order(
        "frontend",
        [
            "Test frontend interactions",
            "Run browser E2E smoke",
            "Frontend pilot smoke",
            "Build frontend",
            "Produce clinic-context execution evidence",
            "Upload frontend remediation evidence",
        ],
    )
    assert_named_order(
        "e2e-db",
        [
            "Run DB-backed full-stack E2E smoke",
            "Upload DB-backed remediation evidence",
        ],
    )
    producer_contracts = {
        "backend": (
            "--unit cross_scope_dto_projection",
            "Validate synthetic test backup and restore",
        ),
        "frontend": ("--unit context_initialization", "Build frontend"),
        "e2e-db": (
            "--unit transitional_workflow_rediscovery",
            "Run DB-backed full-stack E2E smoke",
        ),
    }
    for job_name, (producer_token, prerequisite_name) in producer_contracts.items():
        steps = jobs[job_name]
        producer_indexes = [
            index
            for index, step in enumerate(steps)
            if producer_token
            in "\n".join(
                line
                for line in step["raw"].splitlines()
                if not line.lstrip().startswith("#")
            )
        ]
        prerequisite_index = [
            step.get("name", "") for step in steps
        ].index(prerequisite_name)
        assert len(producer_indexes) == 1, job_name
        assert producer_indexes[0] >= prerequisite_index, job_name

    remediation_names = [
        step.get("name", "") for step in jobs["remediation-evidence"]
    ]
    assert remediation_names.index("Download remediation execution evidence") < remediation_names.index(
        "Validate exact-SHA remediation execution evidence"
    )
    assert remediation_names.index("Validate exact-SHA remediation execution evidence") < remediation_names.index(
        "Produce and validate canonical release evidence"
    )
    assert remediation_names.index("Produce and validate canonical release evidence") < remediation_names.index(
        "Upload canonical release evidence"
    )


def test_valid_exact_sha_release_evidence_passes(tmp_path):
    manifest, now = build_manifest(tmp_path)
    result = validate(manifest, now)
    assert result["source_sha"] == SOURCE_SHA
    assert result["behaviour_units"] == 5
    assert result["coverage_dimensions"] == 6
    assert result["migration_head"] == EXPECTED_MIGRATION_HEAD
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert set(payload) == CANONICAL_TOP_LEVEL_KEYS


@pytest.mark.parametrize(
    "unknown_claims",
    [
        {"production_authorized": True},
        {"future_field": "accepted"},
        {
            "productionReady": True,
            "deploymentApproved": True,
            "realPatientDataAuthorized": True,
        },
    ],
)
def test_rehashed_manifest_with_unknown_top_level_claims_is_rejected(
    tmp_path,
    unknown_claims,
):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.update(unknown_claims))
    with pytest.raises(ReleaseEvidenceError, match="top-level keys"):
        validate(manifest, now)


def test_rehashed_manifest_with_missing_required_top_level_key_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.pop("authorization"))
    with pytest.raises(ReleaseEvidenceError, match="top-level keys"):
        validate(manifest, now)


def test_rehashed_manifest_with_unknown_schema_version_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.update(schema_version=2))
    with pytest.raises(ReleaseEvidenceError, match="Unsupported release-evidence schema"):
        validate(manifest, now)


def test_rehashed_manifest_with_wrong_top_level_type_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.update(authorization="blocked"))
    with pytest.raises(ReleaseEvidenceError, match="invalid types"):
        validate(manifest, now)


def test_reordered_and_reserialized_canonical_manifest_is_accepted(tmp_path):
    manifest, now = build_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    reordered = dict(reversed(list(payload.items())))
    reordered.pop("artifact_hash")
    reordered["artifact_hash"] = _sha256_bytes(_canonical_json(reordered))
    manifest.write_text(
        json.dumps(reordered, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    manifest.with_suffix(manifest.suffix + ".sha256").write_text(
        hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n",
        encoding="ascii",
    )
    assert validate(manifest, now)["authorization_boundaries"] == "validated"


@pytest.mark.parametrize(
    ("workflow_event", "github_sha", "pull_request_head_sha"),
    [
        ("push", SOURCE_SHA, ""),
        ("pull_request", OTHER_SHA, SOURCE_SHA),
    ],
)
def test_checkout_identity_uses_the_event_canonical_sha(
    workflow_event,
    github_sha,
    pull_request_head_sha,
):
    assert validate_checkout_identity(
        workflow_event=workflow_event,
        github_sha=github_sha,
        pull_request_head_sha=pull_request_head_sha,
        checkout_sha=SOURCE_SHA,
    ) == {
        "workflow_event": workflow_event,
        "source_sha": SOURCE_SHA,
    }


@pytest.mark.parametrize(
    ("workflow_event", "github_sha", "pull_request_head_sha", "checkout_sha"),
    [
        ("push", SOURCE_SHA, "", OTHER_SHA),
        ("pull_request", OTHER_SHA, SOURCE_SHA, OTHER_SHA),
        ("pull_request", OTHER_SHA, SOURCE_SHA, ""),
    ],
)
def test_checkout_identity_rejects_missing_or_mismatched_checkout(
    workflow_event,
    github_sha,
    pull_request_head_sha,
    checkout_sha,
):
    with pytest.raises(ReleaseEvidenceError, match="checkout|Checked-out"):
        validate_checkout_identity(
            workflow_event=workflow_event,
            github_sha=github_sha,
            pull_request_head_sha=pull_request_head_sha,
            checkout_sha=checkout_sha,
        )


def test_pull_request_checkout_requires_head_sha():
    with pytest.raises(ReleaseEvidenceError, match="pull_request_head_sha"):
        validate_checkout_identity(
            workflow_event="pull_request",
            github_sha=OTHER_SHA,
            pull_request_head_sha="",
            checkout_sha=SOURCE_SHA,
        )


def test_workflow_explicitly_checks_out_and_verifies_the_canonical_source():
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert_workflow_contract(workflow)
    assert "REMEDIATION_SOURCE_SHA" not in workflow
    assert '--source-sha "$REMEDIATION_CHECKOUT_SHA"' in workflow


@pytest.mark.parametrize(
    "mutation",
    [
        lambda workflow: workflow.replace(
            "      - name: Verify exact source checkout\n",
            "      - uses: actions/setup-node@v7\n"
            "        with:\n"
            '          node-version: "22"\n'
            "      - name: Verify exact source checkout\n",
            1,
        ),
        lambda workflow: workflow.replace(
            "      - name: Verify exact source checkout\n",
            "      - name: Install before verification\n"
            "        run: echo unsafe\n"
            "      - name: Verify exact source checkout\n",
            1,
        ),
        lambda workflow: workflow.replace(
            "      - name: Verify exact source checkout\n",
            "      # - name: Verify exact source checkout\n",
            1,
        ),
        lambda workflow: workflow.replace(
            "      - name: Verify exact source checkout\n",
            "      - name: text mentions Verify exact source checkout\n",
            1,
        ),
        lambda workflow: workflow.replace(
            "      - uses: actions/checkout@v5\n",
            "      - uses: actions/checkout@v5\n"
            "        with:\n"
            "          ref: ${{ github.event.pull_request.head.sha || github.sha }}\n"
            "      - uses: actions/checkout@v5\n",
            1,
        ),
        lambda workflow: workflow.replace(
            "      - name: Upload canonical release evidence\n",
            "      - name: Premature canonical upload\n"
            "        uses: actions/upload-artifact@v6\n"
            "      - name: Upload canonical release evidence\n",
            1,
        ),
        lambda workflow: workflow.replace(
            "      - name: Produce clinic-context execution evidence\n",
            "      - name: Premature evidence production\n"
            "        run: echo --unit context_initialization\n"
            "      - name: Produce clinic-context execution evidence\n",
            1,
        ),
    ],
)
def test_workflow_ordering_mutations_fail_closed(mutation):
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    with pytest.raises(AssertionError):
        assert_workflow_contract(mutation(workflow))


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
            producer_results={
                **CANONICAL_PRODUCER_RESULTS,
                "backend": "failure",
            },
            output_path=tmp_path / "release.json",
            generated_at=now.isoformat(),
        )


@pytest.mark.parametrize("missing_name", sorted(CANONICAL_PRODUCER_RESULTS))
def test_missing_canonical_producer_is_rejected(tmp_path, missing_name):
    evidence_dir, now = build_behaviour_evidence(tmp_path)
    producer_results = dict(CANONICAL_PRODUCER_RESULTS)
    producer_results.pop(missing_name)
    with pytest.raises(ReleaseEvidenceError, match="canonical set"):
        produce_release_manifest(
            evidence_dir=evidence_dir,
            source_sha=SOURCE_SHA,
            workflow_run_id=RUN_ID,
            workflow_name="CI",
            workflow_event="push",
            producer_results=producer_results,
            output_path=tmp_path / "release.json",
            generated_at=now.isoformat(),
        )


@pytest.mark.parametrize(
    "producer_results",
    [
        {},
        {**CANONICAL_PRODUCER_RESULTS, "informational": "success"},
        {"Backend": "success", "frontend": "success", "e2e-db": "success"},
        {" backend": "success", "frontend": "success", "e2e-db": "success"},
    ],
)
def test_noncanonical_producer_set_is_rejected(tmp_path, producer_results):
    evidence_dir, now = build_behaviour_evidence(tmp_path)
    with pytest.raises(ReleaseEvidenceError, match="canonical set"):
        produce_release_manifest(
            evidence_dir=evidence_dir,
            source_sha=SOURCE_SHA,
            workflow_run_id=RUN_ID,
            workflow_name="CI",
            workflow_event="push",
            producer_results=producer_results,
            output_path=tmp_path / "release.json",
            generated_at=now.isoformat(),
        )


def test_duplicate_producer_argument_is_rejected():
    with pytest.raises(ReleaseEvidenceError, match="unique"):
        _producer_results(["backend=success", "backend=success"])


def test_canonical_producer_order_does_not_matter(tmp_path):
    evidence_dir, now = build_behaviour_evidence(tmp_path)
    manifest = tmp_path / "release.json"
    produce_release_manifest(
        evidence_dir=evidence_dir,
        source_sha=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        workflow_name="CI",
        workflow_event="push",
        producer_results={
            "e2e-db": "success",
            "backend": "success",
            "frontend": "success",
        },
        output_path=manifest,
        generated_at=now.isoformat(),
    )
    assert validate_release_manifest(
        manifest_path=manifest,
        source_sha=SOURCE_SHA,
        workflow_run_id=RUN_ID,
        now=now,
    )["authorization_boundaries"] == "validated"


def test_rehashed_manifest_with_incomplete_producers_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(
        manifest,
        lambda payload: payload["ci"]["producer_results"].pop("frontend"),
    )
    with pytest.raises(ReleaseEvidenceError, match="canonical set"):
        validate(manifest, now)


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


def test_canonical_readiness_values_are_accepted(tmp_path):
    manifest, now = build_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["readiness"] == CANONICAL_READINESS
    assert validate(manifest, now)["authorization_boundaries"] == "validated"


def test_readiness_layers_cannot_be_collapsed(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["readiness"].pop("real_patient_data"))
    with pytest.raises(ReleaseEvidenceError, match="canonical evidence-only state"):
        validate(manifest, now)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("code_merge", "ready"),
        ("code_merge", ""),
        ("code_merge", None),
        ("code_merge", True),
        ("code_merge", 1),
        ("deployment", "READY"),
        ("deployment", "passed"),
        ("deployment", False),
        ("production", "ready"),
        ("production", "authorized"),
        ("real_patient_data", "true"),
        ("real_patient_data", True),
    ],
)
def test_rehashed_manifest_with_invalid_readiness_value_is_rejected(
    tmp_path,
    key,
    value,
):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(
        manifest,
        lambda payload: payload["readiness"].update({key: value}),
    )
    with pytest.raises(ReleaseEvidenceError, match="canonical evidence-only state"):
        validate(manifest, now)


def test_rehashed_manifest_with_unknown_readiness_key_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(
        manifest,
        lambda payload: payload["readiness"].update({"unknown": "blocked"}),
    )
    with pytest.raises(ReleaseEvidenceError, match="canonical evidence-only state"):
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
