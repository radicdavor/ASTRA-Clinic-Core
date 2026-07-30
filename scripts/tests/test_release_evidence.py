from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.release_evidence import (
    CANONICAL_PRODUCER_RESULTS,
    CANONICAL_RELEASE_SCHEMA,
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


def schema_paths(schema, path="$"):
    yield path, schema
    if schema["kind"] == "mapping":
        for key, child in schema["properties"].items():
            yield from schema_paths(child, f"{path}.{key}")


def value_at_path(payload, path):
    value = payload
    for key in path.removeprefix("$.").split(".") if path != "$" else []:
        value = value[key]
    return value


EXPECTED_SHA_EXPRESSION = "${{ github.event.pull_request.head.sha || github.sha }}"
VERIFY_STEP_ID = "verify-source-sha"
CANONICAL_VERIFY_RUN = """\
checkout_sha="$(git rev-parse HEAD)"
expected_sha="${{ github.event.pull_request.head.sha || github.sha }}"
if [ -z "$expected_sha" ] || [ "$checkout_sha" != "$expected_sha" ]; then
  echo "Checked-out revision $checkout_sha does not match canonical source $expected_sha"
  exit 1
fi
echo "REMEDIATION_CHECKOUT_SHA=$checkout_sha" >> "$GITHUB_ENV"
"""
EXPECTED_JOBS = {"backend", "frontend", "e2e-db", "remediation-evidence"}
RUNTIME_RECHECK_RUN = """\
set -euo pipefail
expected="${REMEDIATION_CHECKOUT_SHA:?missing verified source SHA}"
actual="$(git rev-parse HEAD)"
workspace="$(git rev-parse --show-toplevel)"
test "$actual" = "$expected"
test "$workspace" = "$GITHUB_WORKSPACE"
git diff --quiet --exit-code HEAD --
git diff --cached --quiet --exit-code HEAD --
for state in MERGE_HEAD REBASE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_LOG; do
  test ! -e "$(git rev-parse --git-path "$state")"
done
echo "REMEDIATION_CHECKOUT_SHA=$actual" >> "$GITHUB_ENV"
"""
RUNTIME_RECHECK_SHA256 = (
    "8443dba506e5ec0d69f7f03fcc027db7f06d75ff50ead803c81f48b0d33cacdf"
)
RUNTIME_RECHECK_IDS = {
    "recheck-source-before-migrations",
    "recheck-source-before-backend-evidence",
    "recheck-source-before-backend-upload",
    "recheck-source-before-frontend-evidence",
    "recheck-source-before-frontend-upload",
    "recheck-source-before-e2e-evidence",
    "recheck-source-before-e2e-upload",
    "recheck-source-before-artifact-intake",
    "recheck-source-before-canonical-evidence",
    "recheck-source-before-canonical-upload",
}
GIT_GLOBAL_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--config-env",
    "--exec-path",
    "--git-dir",
    "--namespace",
    "--work-tree",
}
GIT_GLOBAL_OPTIONS_WITH_INLINE_VALUE = {
    "--config-env=",
    "--exec-path=",
    "--git-dir=",
    "--namespace=",
    "--work-tree=",
}
GIT_GLOBAL_OPTIONS_NO_VALUE = {
    "--glob-pathspecs",
    "--icase-pathspecs",
    "--literal-pathspecs",
    "--no-pager",
    "--noglob-pathspecs",
    "--paginate",
}
ALLOWED_POST_VERIFY_GIT_SUBCOMMANDS = {"diff", "rev-parse"}


class GitHubActionsLoader(yaml.SafeLoader):
    """Safe YAML loader that preserves GitHub's `on` key and rejects duplicates."""


GitHubActionsLoader.yaml_implicit_resolvers = {
    key: list(resolvers)
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for initial in ("o", "O"):
    GitHubActionsLoader.yaml_implicit_resolvers[initial] = [
        resolver
        for resolver in GitHubActionsLoader.yaml_implicit_resolvers.get(initial, [])
        if resolver[0] != "tag:yaml.org,2002:bool"
    ]


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


GitHubActionsLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def parse_workflow(workflow: str) -> dict:
    parsed = yaml.load(workflow, Loader=GitHubActionsLoader)
    assert isinstance(parsed, dict), "workflow must be a YAML mapping"
    assert "on" in parsed, "GitHub Actions `on` key must remain a string"
    jobs = parsed.get("jobs")
    assert isinstance(jobs, dict), "workflow jobs must be a mapping"
    return parsed


def parse_workflow_steps(workflow: str) -> dict[str, list[dict]]:
    parsed = parse_workflow(workflow)
    jobs: dict[str, list[dict]] = {}
    for job_name, job in parsed["jobs"].items():
        assert isinstance(job, dict), f"{job_name}: job must be a mapping"
        steps = job.get("steps")
        assert isinstance(steps, list), f"{job_name}: steps must be a list"
        assert all(isinstance(step, dict) for step in steps), (
            f"{job_name}: every step must be a mapping"
        )
        jobs[job_name] = steps
    return jobs


def normalize_canonical_run(value: str) -> str:
    assert isinstance(value, str), "canonical verify run must be a string"
    return "\n".join(
        line.rstrip()
        for line in value.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    )


def assert_canonical_verify_step(job_name: str, step: dict) -> None:
    assert set(step) == {"name", "id", "shell", "run"}, (
        f"{job_name}: verify step contains non-canonical fields"
    )
    assert step["id"] == VERIFY_STEP_ID, f"{job_name}: verify step ID is not canonical"
    assert step["name"] == "Verify exact source checkout", (
        f"{job_name}: verify step name is not canonical"
    )
    assert step["shell"] == "bash", f"{job_name}: verify shell must be bash"
    assert normalize_canonical_run(step["run"]) == normalize_canonical_run(
        CANONICAL_VERIFY_RUN
    ), f"{job_name}: non-canonical exact-SHA verification command"


def shell_tokens(run: str) -> list[str]:
    lexer = shlex.shlex(run, posix=True, punctuation_chars=";&|(){}")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError as exc:
        raise AssertionError(f"unsupported post-verify shell syntax: {exc}") from exc


def is_git_executable(token: str) -> bool:
    normalized = token.replace("\\", "/").rstrip("/")
    return normalized == "git" or normalized.endswith("/git")


def git_subcommands(run: str) -> list[str]:
    tokens = shell_tokens(run)
    subcommands = []
    for git_index, token in enumerate(tokens):
        if not is_git_executable(token):
            continue
        index = git_index + 1
        while index < len(tokens):
            option = tokens[index]
            if option in GIT_GLOBAL_OPTIONS_WITH_VALUE:
                assert index + 1 < len(tokens), (
                    f"Git global option {option} is missing its value"
                )
                index += 2
                continue
            if any(
                option.startswith(prefix)
                for prefix in GIT_GLOBAL_OPTIONS_WITH_INLINE_VALUE
            ):
                index += 1
                continue
            if option in GIT_GLOBAL_OPTIONS_NO_VALUE:
                index += 1
                continue
            assert not option.startswith("-"), (
                f"unsupported Git global option after verification: {option}"
            )
            assert option not in {";", "&&", "||", "|", "(", ")", "{", "}"}, (
                "Git command is missing a subcommand"
            )
            subcommands.append(option)
            break
        else:
            raise AssertionError("Git command is missing a subcommand")
    for nested in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", run, flags=re.DOTALL):
        nested_command = next(value for value in nested if value)
        subcommands.extend(git_subcommands(nested_command))
    return subcommands


def assert_canonical_runtime_recheck_step(job_name: str, step: dict) -> None:
    assert set(step) == {"name", "id", "shell", "run"}, (
        f"{job_name}: runtime integrity recheck contains non-canonical fields"
    )
    assert step["id"] in RUNTIME_RECHECK_IDS, (
        f"{job_name}: runtime integrity recheck ID is not canonical"
    )
    assert step["name"] == "Recheck source integrity", (
        f"{job_name}: runtime integrity recheck name is not canonical"
    )
    assert step["shell"] == "bash", (
        f"{job_name}: runtime integrity recheck shell must be bash"
    )
    assert normalize_canonical_run(step["run"]) == normalize_canonical_run(
        RUNTIME_RECHECK_RUN
    ), f"{job_name}: non-canonical runtime source-integrity recheck"
    assert (
        hashlib.sha256(
            normalize_canonical_run(step["run"]).encode("utf-8")
        ).hexdigest()
        == RUNTIME_RECHECK_SHA256
    ), f"{job_name}: runtime source-integrity recheck hash mismatch"


def assert_no_post_verify_repository_mutation(job_name: str, steps: list[dict]) -> None:
    for index, step in enumerate(steps[2:], start=2):
        uses = step.get("uses", "")
        assert not (
            isinstance(uses, str) and uses.startswith("actions/checkout@")
        ), f"{job_name}: later checkout at step {index}"
        run = step.get("run")
        if isinstance(run, str):
            for subcommand in git_subcommands(run):
                assert subcommand in ALLOWED_POST_VERIFY_GIT_SUBCOMMANDS, (
                    f"{job_name}: repository-changing or unknown Git subcommand "
                    f"after verification: {subcommand}"
                )
            if step.get("id") in RUNTIME_RECHECK_IDS:
                assert_canonical_runtime_recheck_step(job_name, step)
            else:
                assert not re.search(
                    r"(^|\n)\s*(?:export\s+)?REMEDIATION_CHECKOUT_SHA\s*=",
                    run,
                ), f"{job_name}: verified SHA is redefined after verification"
                assert not re.search(
                    r"REMEDIATION_CHECKOUT_SHA=.*>>\s*[\"']?\$GITHUB_ENV",
                    run,
                ), f"{job_name}: verified SHA environment value is overwritten"
        env = step.get("env", {})
        assert not (
            isinstance(env, dict) and "REMEDIATION_CHECKOUT_SHA" in env
        ), f"{job_name}: verified SHA is shadowed by step environment"
        if isinstance(uses, str) and uses.startswith("actions/download-artifact@"):
            download_path = step.get("with", {}).get("path")
            assert (
                isinstance(download_path, str)
                and download_path.startswith(".remediation-evidence/")
            ), f"{job_name}: artifact download may overwrite repository root"


def assert_recheck_immediately_before(
    job_name: str,
    steps: list[dict],
    target_name: str,
    recheck_id: str,
) -> None:
    target_indexes = [
        index for index, step in enumerate(steps) if step.get("name") == target_name
    ]
    assert len(target_indexes) == 1, f"{job_name}: missing unique {target_name!r} step"
    target_index = target_indexes[0]
    assert target_index > 0, f"{job_name}: {target_name!r} cannot be first"
    recheck = steps[target_index - 1]
    assert recheck.get("id") == recheck_id, (
        f"{job_name}: runtime integrity recheck must immediately precede "
        f"{target_name!r}"
    )
    assert_canonical_runtime_recheck_step(job_name, recheck)


def assert_workflow_contract(workflow: str) -> None:
    parsed = parse_workflow(workflow)
    jobs = parse_workflow_steps(workflow)
    assert EXPECTED_JOBS <= set(jobs)

    for job_name in EXPECTED_JOBS:
        job = parsed["jobs"][job_name]
        assert "REMEDIATION_CHECKOUT_SHA" not in job.get("env", {}), (
            f"{job_name}: verified SHA must not be predefined at job scope"
        )
        steps = jobs[job_name]
        checkout_indexes = [
            index
            for index, step in enumerate(steps)
            if isinstance(step.get("uses"), str)
            and step["uses"].startswith("actions/checkout@")
        ]
        verify_indexes = [
            index
            for index, step in enumerate(steps)
            if step.get("id") == VERIFY_STEP_ID
        ]
        assert checkout_indexes == [0], f"{job_name}: checkout must occur exactly once first"
        assert verify_indexes == [1], (
            f"{job_name}: canonical verification must immediately follow checkout"
        )
        checkout = steps[0]
        verify = steps[1]
        assert set(checkout) == {"uses", "with"}, (
            f"{job_name}: checkout step contains non-canonical fields"
        )
        assert checkout["uses"] == "actions/checkout@v5", (
            f"{job_name}: checkout action is not canonical"
        )
        assert checkout["with"] == {"ref": EXPECTED_SHA_EXPRESSION}, (
            f"{job_name}: checkout ref is not the event-derived source SHA"
        )
        assert_canonical_verify_step(job_name, verify)
        assert all(
            index > verify_indexes[0]
            for index, step in enumerate(steps)
            if isinstance(step.get("uses"), str)
            and step["uses"].startswith(("actions/setup-", "actions/download-artifact@"))
        ), f"{job_name}: runtime or artifact action precedes source verification"
        assert_no_post_verify_repository_mutation(job_name, steps)
        upload_indexes = [
            index
            for index, step in enumerate(steps)
            if isinstance(step.get("uses"), str)
            and step["uses"].startswith("actions/upload-artifact@")
        ]
        assert upload_indexes == [len(steps) - 1], (
            f"{job_name}: artifact upload must be the final step"
        )
        for step in steps:
            run = step.get("run", "")
            if isinstance(run, str) and (
                "validate_pr3_remediation_closure.py produce" in run
                or "release_evidence.py produce" in run
            ):
                assert '--source-sha "$REMEDIATION_CHECKOUT_SHA"' in run, (
                    f"{job_name}: evidence producer must use the verified checkout SHA"
                )

    required_boundaries = {
        "backend": [
            ("Run database migrations", "recheck-source-before-migrations"),
            (
                "Produce episode and proxy execution evidence",
                "recheck-source-before-backend-evidence",
            ),
            (
                "Upload backend remediation evidence",
                "recheck-source-before-backend-upload",
            ),
        ],
        "frontend": [
            (
                "Produce clinic-context execution evidence",
                "recheck-source-before-frontend-evidence",
            ),
            (
                "Upload frontend remediation evidence",
                "recheck-source-before-frontend-upload",
            ),
        ],
        "e2e-db": [
            (
                "Run DB-backed full-stack E2E smoke",
                "recheck-source-before-e2e-evidence",
            ),
            (
                "Upload DB-backed remediation evidence",
                "recheck-source-before-e2e-upload",
            ),
        ],
        "remediation-evidence": [
            (
                "Download remediation execution evidence",
                "recheck-source-before-artifact-intake",
            ),
            (
                "Produce and validate canonical release evidence",
                "recheck-source-before-canonical-evidence",
            ),
            (
                "Upload canonical release evidence",
                "recheck-source-before-canonical-upload",
            ),
        ],
    }
    for job_name, boundaries in required_boundaries.items():
        for target_name, recheck_id in boundaries:
            assert_recheck_immediately_before(
                job_name,
                jobs[job_name],
                target_name,
                recheck_id,
            )

    def step_index(job_name: str, token: str) -> int:
        if token.startswith("uses:"):
            predicate = lambda step: token.removeprefix("uses:") in step.get("uses", "")
        elif token.startswith("artifact:"):
            predicate = lambda step: (
                step.get("with", {}).get("name") == token.removeprefix("artifact:")
            )
        else:
            predicate = lambda step: token in step.get("run", "")
        indexes = [
            index
            for index, step in enumerate(jobs[job_name])
            if predicate(step)
        ]
        assert len(indexes) == 1, f"{job_name}: expected one executable step for {token}"
        return indexes[0]

    def assert_semantic_order(job_name: str, tokens: list[str]) -> None:
        indexes = [step_index(job_name, token) for token in tokens]
        assert indexes == sorted(indexes), f"{job_name}: semantic step order changed"

    assert_semantic_order(
        "backend",
        [
            "test_pr3_scope_audit_blockers.py",
            "run_test_gate.py fast",
            '-m "not integration"',
            "tests/integration",
            "validate_test_backup_restore.sh",
            "--unit cross_scope_dto_projection",
            "artifact:remediation-evidence-backend",
        ],
    )
    assert_semantic_order(
        "frontend",
        [
            "npm test -- --run",
            "npm run e2e",
            "npm run smoke",
            "npm run build",
            "--unit context_initialization",
            "artifact:remediation-evidence-frontend",
        ],
    )
    assert_semantic_order(
        "e2e-db",
        [
            "npm run e2e:db",
            "artifact:remediation-evidence-e2e-db",
        ],
    )
    producer_contracts = {
        "backend": (
            "--unit cross_scope_dto_projection",
            "validate_test_backup_restore.sh",
        ),
        "frontend": ("--unit context_initialization", "npm run build"),
        "e2e-db": (
            "--unit transitional_workflow_rediscovery",
            "npm run e2e:db",
        ),
    }
    for job_name, (producer_token, prerequisite_token) in producer_contracts.items():
        steps = jobs[job_name]
        producer_indexes = [
            index
            for index, step in enumerate(steps)
            if producer_token in step.get("run", "")
        ]
        prerequisite_index = step_index(job_name, prerequisite_token)
        assert len(producer_indexes) == 1, job_name
        assert producer_indexes[0] >= prerequisite_index, job_name

    assert_semantic_order(
        "remediation-evidence",
        [
            "uses:actions/download-artifact@",
            "validate_pr3_remediation_closure.py validate",
            "release_evidence.py produce",
            "artifact:release-evidence",
        ],
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
    with pytest.raises(ReleaseEvidenceError, match=r"\$: mapping keys"):
        validate(manifest, now)


def test_rehashed_manifest_with_missing_required_top_level_key_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.pop("authorization"))
    with pytest.raises(ReleaseEvidenceError, match=r"\$: mapping keys"):
        validate(manifest, now)


def test_rehashed_manifest_with_unknown_schema_version_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.update(schema_version=2))
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.schema_version: expected canonical"):
        validate(manifest, now)


def test_rehashed_manifest_with_wrong_top_level_type_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload.update(authorization="blocked"))
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.authorization: expected mapping"):
        validate(manifest, now)


def test_every_mapping_node_rejects_rehashed_unknown_claim(tmp_path):
    manifest, now = build_manifest(tmp_path)
    original = json.loads(manifest.read_text(encoding="utf-8"))
    mapping_paths = [
        path
        for path, schema in schema_paths(CANONICAL_RELEASE_SCHEMA)
        if schema["kind"] == "mapping"
    ]
    assert mapping_paths == [
        "$",
        "$.authorization",
        "$.ci",
        "$.ci.producer_results",
        "$.credential_rotation",
        "$.dependencies",
        "$.deployment_validation",
        "$.findings",
        "$.migrations",
        "$.producer",
        "$.readiness",
        "$.recovery",
        "$.review",
        "$.security",
        "$.tests",
        "$.usability",
    ]
    for path in mapping_paths:
        manifest.write_text(
            json.dumps(original, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest.with_suffix(manifest.suffix + ".sha256").write_text(
            hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n",
            encoding="ascii",
        )

        def add_unknown(payload):
            value_at_path(payload, path)["__unexpected_contract_claim__"] = True

        rewrite_manifest(manifest, add_unknown)
        with pytest.raises(ReleaseEvidenceError, match=re.escape(path)):
            validate(manifest, now)


def test_every_mapping_node_rejects_missing_key_and_non_mapping_value(tmp_path):
    manifest, now = build_manifest(tmp_path)
    original = json.loads(manifest.read_text(encoding="utf-8"))
    mapping_paths = [
        path
        for path, schema in schema_paths(CANONICAL_RELEASE_SCHEMA)
        if schema["kind"] == "mapping"
    ]
    for path in mapping_paths:
        expected_keys = sorted(value_at_path(original, path))
        if path == "$":
            expected_keys.remove("artifact_hash")
        for mutation in ("missing", "wrong_type"):
            manifest.write_text(
                json.dumps(original, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            manifest.with_suffix(manifest.suffix + ".sha256").write_text(
                hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n",
                encoding="ascii",
            )

            def mutate_mapping(payload):
                if path == "$":
                    if mutation == "missing":
                        payload.pop(expected_keys[0])
                    else:
                        payload["authorization"] = []
                    return
                parent_path, key = path.rsplit(".", 1)
                if mutation == "missing":
                    value_at_path(payload, path).pop(expected_keys[0])
                else:
                    value_at_path(payload, parent_path)[key] = []

            rewrite_manifest(manifest, mutate_mapping)
            expected_path = path if mutation == "missing" else (
                "$.authorization" if path == "$" else path
            )
            with pytest.raises(ReleaseEvidenceError, match=re.escape(expected_path)):
                validate(manifest, now)


@pytest.mark.parametrize(
    ("path", "key"),
    [
        ("$.authorization", "production_authorized"),
        ("$.security", "formal_security_approved"),
        ("$.ci", "deployment_authorized"),
        ("$.tests", "production_ready"),
        ("$.producer", "trusted"),
    ],
)
def test_rehashed_nested_authority_claims_are_rejected(tmp_path, path, key):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(
        manifest,
        lambda payload: value_at_path(payload, path).update({key: True}),
    )
    with pytest.raises(
        ReleaseEvidenceError,
        match=rf"{re.escape(path)}: mapping keys.*{key}",
    ):
        validate(manifest, now)


def test_every_schema_field_rejects_wrong_nested_type(tmp_path):
    manifest, now = build_manifest(tmp_path)
    original = json.loads(manifest.read_text(encoding="utf-8"))
    leaf_paths = [
        path
        for path, schema in schema_paths(CANONICAL_RELEASE_SCHEMA)
        if schema["kind"] != "mapping" and path != "$.artifact_hash"
    ]
    for path in leaf_paths:
        manifest.write_text(
            json.dumps(original, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest.with_suffix(manifest.suffix + ".sha256").write_text(
            hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n",
            encoding="ascii",
        )

        def replace_with_wrong_type(payload):
            parent_path, key = path.rsplit(".", 1)
            current = value_at_path(payload, path)
            replacement = (
                {"wrong": "type"}
                if isinstance(current, (str, int, bool)) or current is None
                else "wrong-type"
            )
            value_at_path(payload, parent_path)[key] = replacement

        rewrite_manifest(manifest, replace_with_wrong_type)
        with pytest.raises(ReleaseEvidenceError, match=re.escape(path)):
            validate(manifest, now)


def test_every_closed_literal_rejects_same_type_noncanonical_value(tmp_path):
    manifest, now = build_manifest(tmp_path)
    original = json.loads(manifest.read_text(encoding="utf-8"))
    literal_paths = [
        path
        for path, schema in schema_paths(CANONICAL_RELEASE_SCHEMA)
        if schema["kind"] == "literal" and path != "$.artifact_hash"
    ]
    for path in literal_paths:
        manifest.write_text(
            json.dumps(original, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest.with_suffix(manifest.suffix + ".sha256").write_text(
            hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n",
            encoding="ascii",
        )

        def replace_literal(payload):
            parent_path, key = path.rsplit(".", 1)
            current = value_at_path(payload, path)
            if type(current) is bool:
                replacement = not current
            elif type(current) is int:
                replacement = current + 1
            else:
                replacement = "__noncanonical_value__"
            value_at_path(payload, parent_path)[key] = replacement

        rewrite_manifest(manifest, replace_literal)
        with pytest.raises(ReleaseEvidenceError, match=re.escape(path)):
            validate(manifest, now)


def test_duplicate_nested_json_key_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    content = manifest.read_text(encoding="utf-8")
    content = content.replace(
        '"production": false,',
        '"production": false, "production": false,',
        1,
    )
    manifest.write_text(content, encoding="utf-8")
    manifest.with_suffix(manifest.suffix + ".sha256").write_text(
        hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n",
        encoding="ascii",
    )
    with pytest.raises(ReleaseEvidenceError, match="duplicate JSON key 'production'"):
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


def mutate_workflow(workflow: str, mutation: str) -> str:
    parsed = parse_workflow(workflow)
    jobs = parsed["jobs"]
    backend = jobs["backend"]["steps"]
    verify = backend[1]

    if mutation == "inert_variable_tokens":
        verify["run"] = (
            "ignored='git rev-parse HEAD "
            "${{ github.event.pull_request.head.sha || github.sha }} "
            "exit 1 REMEDIATION_CHECKOUT_SHA'\n"
            "echo verification-bypassed\n"
        )
    elif mutation == "comment_tokens":
        verify["run"] = (
            "# git rev-parse HEAD "
            "${{ github.event.pull_request.head.sha || github.sha }} "
            "exit 1 REMEDIATION_CHECKOUT_SHA\n"
            "echo verification-bypassed\n"
        )
    elif mutation == "name_tokens":
        verify["name"] = (
            "git rev-parse HEAD "
            "${{ github.event.pull_request.head.sha || github.sha }} "
            "exit 1 REMEDIATION_CHECKOUT_SHA"
        )
        verify["run"] = "echo verification-bypassed\n"
    elif mutation == "echo_rev_parse":
        verify["run"] = 'echo "git rev-parse HEAD"\n'
    elif mutation == "exit_zero_before_verify":
        verify["run"] = "exit 0\n" + CANONICAL_VERIFY_RUN
    elif mutation == "unexecuted_function":
        verify["run"] = (
            "verify_source() {\n"
            + "\n".join(f"  {line}" for line in CANONICAL_VERIFY_RUN.splitlines())
            + "\n}\n"
            "echo verification-bypassed\n"
        )
    elif mutation == "unexecuted_heredoc":
        verify["run"] = "cat <<'VERIFY'\n" + CANONICAL_VERIFY_RUN + "VERIFY\n"
    elif mutation == "or_true":
        verify["run"] = CANONICAL_VERIFY_RUN + "false || true\n"
    elif mutation == "set_plus_e":
        verify["run"] = "set +e\n" + CANONICAL_VERIFY_RUN.replace("exit 1", "false")
    elif mutation == "continue_on_error":
        verify["continue-on-error"] = True
    elif mutation == "false_if":
        verify["if"] = "${{ false }}"
    elif mutation == "setup_before_verify":
        backend[1], backend[2] = backend[2], backend[1]
    elif mutation == "run_before_verify":
        backend.insert(1, {"name": "Unsafe preflight", "run": "echo unsafe"})
    elif mutation == "duplicate_verify_id":
        backend[2]["id"] = VERIFY_STEP_ID
    elif mutation == "duplicate_checkout":
        backend.insert(
            1,
            {"uses": "actions/checkout@v5", "with": {"ref": EXPECTED_SHA_EXPRESSION}},
        )
    elif mutation == "later_checkout":
        backend.insert(
            2,
            {"uses": "actions/checkout@v5", "with": {"ref": EXPECTED_SHA_EXPRESSION}},
        )
    elif mutation == "checkout_without_ref":
        backend[0].pop("with")
    elif mutation == "pull_request_merge_ref":
        backend[0]["with"]["ref"] = "refs/pull/${{ github.event.number }}/merge"
    elif mutation == "empty_expected_sha":
        verify["run"] = CANONICAL_VERIFY_RUN.replace(
            'expected_sha="${{ github.event.pull_request.head.sha || github.sha }}"',
            'expected_sha=""',
        )
    elif mutation == "mismatch_without_failure":
        verify["run"] = (
            'checkout_sha="$(git rev-parse HEAD)"\n'
            'expected_sha="${{ github.event.pull_request.head.sha || github.sha }}"\n'
            'echo "unchecked $checkout_sha $expected_sha"\n'
            'echo "REMEDIATION_CHECKOUT_SHA=$checkout_sha" >> "$GITHUB_ENV"\n'
        )
    elif mutation == "evidence_before_tests":
        frontend = jobs["frontend"]["steps"]
        producer_index = next(
            index
            for index, step in enumerate(frontend)
            if step.get("name") == "Produce clinic-context execution evidence"
        )
        frontend.insert(5, frontend.pop(producer_index))
    elif mutation == "upload_before_validation":
        remediation = jobs["remediation-evidence"]["steps"]
        upload_index = next(
            index
            for index, step in enumerate(remediation)
            if step.get("name") == "Upload canonical release evidence"
        )
        remediation.insert(5, remediation.pop(upload_index))
    elif mutation == "git_reset_after_verify":
        backend.insert(2, {"name": "Replace source", "run": "git reset --hard HEAD^"})
    elif mutation == "removed_runtime_recheck":
        recheck_index = next(
            index
            for index, step in enumerate(backend)
            if step.get("id") == "recheck-source-before-migrations"
        )
        backend.pop(recheck_index)
    elif mutation == "runtime_recheck_after_evidence":
        recheck_index = next(
            index
            for index, step in enumerate(backend)
            if step.get("id") == "recheck-source-before-backend-evidence"
        )
        producer_index = next(
            index
            for index, step in enumerate(backend)
            if step.get("name") == "Produce episode and proxy execution evidence"
        )
        recheck = backend.pop(recheck_index)
        producer_index = next(
            index
            for index, step in enumerate(backend)
            if step.get("name") == "Produce episode and proxy execution evidence"
        )
        backend.insert(producer_index + 1, recheck)
    elif mutation == "runtime_recheck_or_true":
        recheck = next(
            step
            for step in backend
            if step.get("id") == "recheck-source-before-migrations"
        )
        recheck["run"] = RUNTIME_RECHECK_RUN + "false || true\n"
    elif mutation == "runtime_recheck_continue_on_error":
        recheck = next(
            step
            for step in backend
            if step.get("id") == "recheck-source-before-migrations"
        )
        recheck["continue-on-error"] = True
    elif mutation == "runtime_recheck_false_if":
        recheck = next(
            step
            for step in backend
            if step.get("id") == "recheck-source-before-migrations"
        )
        recheck["if"] = "${{ false }}"
    elif mutation == "runtime_recheck_inert_tokens":
        recheck = next(
            step
            for step in backend
            if step.get("id") == "recheck-source-before-migrations"
        )
        recheck["run"] = (
            "ignored='git rev-parse HEAD git diff --quiet "
            "REMEDIATION_CHECKOUT_SHA'\n"
            "echo integrity-bypassed\n"
        )
    else:
        raise AssertionError(f"unknown test mutation {mutation}")

    return yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("inert_variable_tokens", "non-canonical exact-SHA verification command"),
        ("comment_tokens", "non-canonical exact-SHA verification command"),
        ("name_tokens", "verify step name is not canonical"),
        ("echo_rev_parse", "non-canonical exact-SHA verification command"),
        ("exit_zero_before_verify", "non-canonical exact-SHA verification command"),
        ("unexecuted_function", "non-canonical exact-SHA verification command"),
        ("unexecuted_heredoc", "non-canonical exact-SHA verification command"),
        ("or_true", "non-canonical exact-SHA verification command"),
        ("set_plus_e", "non-canonical exact-SHA verification command"),
        ("continue_on_error", "verify step contains non-canonical fields"),
        ("false_if", "verify step contains non-canonical fields"),
        ("setup_before_verify", "canonical verification must immediately follow checkout"),
        ("run_before_verify", "canonical verification must immediately follow checkout"),
        ("duplicate_verify_id", "canonical verification must immediately follow checkout"),
        ("duplicate_checkout", "checkout must occur exactly once first"),
        ("later_checkout", "checkout must occur exactly once first"),
        ("checkout_without_ref", "checkout step contains non-canonical fields"),
        ("pull_request_merge_ref", "checkout ref is not the event-derived source SHA"),
        ("empty_expected_sha", "non-canonical exact-SHA verification command"),
        ("mismatch_without_failure", "non-canonical exact-SHA verification command"),
        ("evidence_before_tests", "frontend"),
        ("upload_before_validation", "remediation-evidence"),
        ("git_reset_after_verify", "repository-changing or unknown Git subcommand"),
        ("removed_runtime_recheck", "runtime integrity recheck must immediately precede"),
        (
            "runtime_recheck_after_evidence",
            "runtime integrity recheck must immediately precede",
        ),
        ("runtime_recheck_or_true", "non-canonical runtime source-integrity recheck"),
        (
            "runtime_recheck_continue_on_error",
            "runtime integrity recheck contains non-canonical fields",
        ),
        (
            "runtime_recheck_false_if",
            "runtime integrity recheck contains non-canonical fields",
        ),
        (
            "runtime_recheck_inert_tokens",
            "non-canonical runtime source-integrity recheck",
        ),
    ],
)
def test_workflow_ordering_mutations_fail_closed(mutation, error):
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    mutated = mutate_workflow(workflow, mutation)
    parse_workflow(mutated)
    with pytest.raises(AssertionError, match=error):
        assert_workflow_contract(mutated)


def test_workflow_contract_accepts_crlf_and_trailing_whitespace():
    workflow = (Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert_workflow_contract(workflow.replace("\n", "  \r\n"))


@pytest.mark.parametrize(
    "command",
    [
        'git -C "$GITHUB_WORKSPACE" reset --hard HEAD^',
        'cd "$GITHUB_WORKSPACE" && git reset --hard HEAD^',
        "command git reset --hard HEAD^",
        "env git reset --hard HEAD^",
        "env FOO=bar git reset --hard HEAD^",
        'cd "$GITHUB_WORKSPACE"; git reset --hard HEAD^',
        'cd "$GITHUB_WORKSPACE"\ngit reset --hard HEAD^',
        "true && git reset --hard HEAD^",
        (
            'git --work-tree="$GITHUB_WORKSPACE" '
            '--git-dir="$GITHUB_WORKSPACE/.git" reset --hard HEAD^'
        ),
        '/usr/bin/git -C "$GITHUB_WORKSPACE" reset --hard HEAD^',
        '"$GIT_EXEC_PATH/git" reset --hard HEAD^',
        '(cd "$GITHUB_WORKSPACE" && git reset --hard HEAD^)',
        '{ cd "$GITHUB_WORKSPACE"; git reset --hard HEAD^; }',
        "if true; then git reset --hard HEAD^; fi",
        "git -c advice.detachedHead=false reset --hard HEAD^",
        "git update-ref refs/heads/main HEAD^",
        "git read-tree HEAD^",
        "git checkout-index --all --force",
        "git apply change.patch",
        'value="$(git reset --hard HEAD^)"',
        "value=`git reset --hard HEAD^`",
    ],
)
def test_post_verify_git_mutations_with_options_and_prefixes_fail_closed(command):
    workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"
    parsed = parse_workflow(workflow_path.read_text(encoding="utf-8"))
    parsed["jobs"]["backend"]["steps"].insert(
        2,
        {"name": "Mutate verified source", "shell": "bash", "run": command},
    )
    mutated = yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True)
    parse_workflow(mutated)
    with pytest.raises(
        AssertionError,
        match="repository-changing or unknown Git subcommand",
    ):
        assert_workflow_contract(mutated)


@pytest.mark.parametrize(
    "command",
    [
        "git frobnicate HEAD",
        "git --unknown-global-option reset --hard HEAD^",
    ],
)
def test_unknown_post_verify_git_surface_fails_closed(command):
    workflow_path = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"
    parsed = parse_workflow(workflow_path.read_text(encoding="utf-8"))
    parsed["jobs"]["backend"]["steps"].insert(
        2,
        {"name": "Unsupported Git surface", "shell": "bash", "run": command},
    )
    mutated = yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True)
    with pytest.raises(AssertionError, match="unknown Git subcommand|global option"):
        assert_workflow_contract(mutated)


def _git_bash() -> str:
    if os.name != "nt":
        return "/bin/bash"
    candidates = [
        Path(r"C:\Program Files\Git\bin\bash.exe"),
        Path(r"C:\Program Files\Git\usr\bin\bash.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    pytest.skip("Git Bash is unavailable for the runtime integrity attack test")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.mark.parametrize(
    "attack",
    [
        'git -C "$GITHUB_WORKSPACE" reset --hard HEAD^',
        'cd "$GITHUB_WORKSPACE" && git reset --hard HEAD^',
    ],
)
def test_runtime_recheck_blocks_post_verify_head_mutation(tmp_path, attack):
    repo = tmp_path / "runtime-attack"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "ASTRA CI")
    _git(repo, "config", "user.email", "astra-ci@example.invalid")
    tracked = repo / "tracked.txt"
    tracked.write_text("first\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "first")
    tracked.write_text("second\n", encoding="utf-8")
    _git(repo, "commit", "-am", "second")
    expected = _git(repo, "rev-parse", "HEAD")
    workspace = _git(repo, "rev-parse", "--show-toplevel")
    marker = repo / "evidence-produced"
    script = f"{attack}\n{RUNTIME_RECHECK_RUN}\nprintf evidence > \"$EVIDENCE_MARKER\"\n"
    env = {
        **os.environ,
        "GITHUB_ENV": str(repo / "github-env"),
        "GITHUB_WORKSPACE": workspace,
        "REMEDIATION_CHECKOUT_SHA": expected,
        "EVIDENCE_MARKER": str(marker),
    }
    result = subprocess.run(
        [_git_bash(), "-c", script],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not marker.exists()


@pytest.mark.parametrize("staged", [False, True])
def test_runtime_recheck_blocks_tracked_tree_or_index_drift(tmp_path, staged):
    repo = tmp_path / "runtime-drift"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "ASTRA CI")
    _git(repo, "config", "user.email", "astra-ci@example.invalid")
    tracked = repo / "tracked.txt"
    tracked.write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    expected = _git(repo, "rev-parse", "HEAD")
    workspace = _git(repo, "rev-parse", "--show-toplevel")
    tracked.write_text("drift\n", encoding="utf-8")
    if staged:
        _git(repo, "add", "tracked.txt")
    env = {
        **os.environ,
        "GITHUB_ENV": str(repo / "github-env"),
        "GITHUB_WORKSPACE": workspace,
        "REMEDIATION_CHECKOUT_SHA": expected,
    }
    result = subprocess.run(
        [_git_bash(), "-c", RUNTIME_RECHECK_RUN],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_runtime_recheck_accepts_clean_expected_checkout(tmp_path):
    repo = tmp_path / "runtime-clean"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "ASTRA CI")
    _git(repo, "config", "user.email", "astra-ci@example.invalid")
    (repo / "tracked.txt").write_text("clean\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    expected = _git(repo, "rev-parse", "HEAD")
    workspace = _git(repo, "rev-parse", "--show-toplevel")
    github_env = repo / "github-env"
    env = {
        **os.environ,
        "GITHUB_ENV": str(github_env),
        "GITHUB_WORKSPACE": workspace,
        "REMEDIATION_CHECKOUT_SHA": expected,
    }
    result = subprocess.run(
        [_git_bash(), "-c", RUNTIME_RECHECK_RUN],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert github_env.read_text(encoding="utf-8") == (
        f"REMEDIATION_CHECKOUT_SHA={expected}\n"
    )


def test_github_actions_loader_preserves_on_and_rejects_duplicate_keys():
    parsed = parse_workflow("name: CI\non:\n  push:\njobs: {}\n")
    assert "on" in parsed
    with pytest.raises(yaml.constructor.ConstructorError, match="duplicate key"):
        parse_workflow(
            "name: CI\non:\n  push:\njobs:\n  backend: {}\n  backend: {}\n"
        )


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
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.ci\.producer_results"):
        validate(manifest, now)


def test_stale_manifest_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    with pytest.raises(ReleaseEvidenceError, match="stale"):
        validate(manifest, now + timedelta(hours=25))


def test_internal_artifact_hash_mismatch_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["generated_at"] = (now - timedelta(minutes=1)).isoformat()
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
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.migrations\.observed_head"):
        validate(manifest, now)


def test_false_formal_security_closure_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["security"].update(formal_codex_security_closure="approved", sealed=True))
    with pytest.raises(
        ReleaseEvidenceError,
        match=r"\$\.security\.formal_codex_security_closure",
    ):
        validate(manifest, now)


def test_unauthorized_production_claim_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["authorization"].update(production=True))
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.authorization\.production"):
        validate(manifest, now)


def test_canonical_readiness_values_are_accepted(tmp_path):
    manifest, now = build_manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["readiness"] == CANONICAL_READINESS
    assert validate(manifest, now)["authorization_boundaries"] == "validated"


def test_readiness_layers_cannot_be_collapsed(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(manifest, lambda payload: payload["readiness"].pop("real_patient_data"))
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.readiness"):
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
    with pytest.raises(ReleaseEvidenceError, match=rf"\$\.readiness\.{key}"):
        validate(manifest, now)


def test_rehashed_manifest_with_unknown_readiness_key_is_rejected(tmp_path):
    manifest, now = build_manifest(tmp_path)
    rewrite_manifest(
        manifest,
        lambda payload: payload["readiness"].update({"unknown": "blocked"}),
    )
    with pytest.raises(ReleaseEvidenceError, match=r"\$\.readiness"):
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
