from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml


TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))

from test_release_evidence import (  # noqa: E402
    ALLOWED_POST_VERIFY_GIT_SUBCOMMANDS,
    CANONICAL_VERIFY_RUN,
    EXPECTED_SHA_EXPRESSION,
    RUNTIME_RECHECK_RUN,
    RUNTIME_RECHECK_SHA256,
    VERIFY_STEP_ID,
    assert_canonical_verify_step,
    git_subcommands,
    normalize_canonical_run,
    parse_workflow,
    parse_workflow_steps,
)


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "recovery.yml"
GIT_EXECUTABLE = Path(shutil.which("git") or "git")
GIT_BASH = (
    GIT_EXECUTABLE.parent.parent / "bin" / "bash.exe"
    if os.name == "nt"
    else Path(shutil.which("bash") or "/bin/bash")
)
EXPECTED_JOBS = {"recovery", "recovery-evidence"}
RECHECK_IDS = {
    "recheck-source-before-recovery-matrix",
    "recheck-source-before-recovery-evidence",
    "recheck-source-before-recovery-upload",
    "recheck-source-before-recovery-artifact-intake",
    "recheck-source-before-recovery-validation",
}
BOUNDARIES = {
    "recovery": {
        "Run disposable PostgreSQL recovery matrix":
            "recheck-source-before-recovery-matrix",
        "Produce recovery execution evidence":
            "recheck-source-before-recovery-evidence",
        "Upload recovery execution evidence":
            "recheck-source-before-recovery-upload",
    },
    "recovery-evidence": {
        "Download recovery evidence":
            "recheck-source-before-recovery-artifact-intake",
        "Validate exact-SHA recovery evidence":
            "recheck-source-before-recovery-validation",
    },
}


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def dump_workflow(parsed: dict) -> str:
    return yaml.safe_dump(parsed, sort_keys=False, allow_unicode=True)


def step_named(steps: list[dict], name: str) -> dict:
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"missing unique {name!r} step"
    return matches[0]


def assert_runtime_recheck(job_name: str, step: dict) -> None:
    assert set(step) == {"name", "id", "shell", "run"}
    assert step["name"] == "Recheck source integrity"
    assert step["id"] in RECHECK_IDS
    assert step["shell"] == "bash"
    assert normalize_canonical_run(step["run"]) == normalize_canonical_run(
        RUNTIME_RECHECK_RUN
    ), f"{job_name}: non-canonical runtime source-integrity recheck"
    import hashlib

    assert hashlib.sha256(
        normalize_canonical_run(step["run"]).encode("utf-8")
    ).hexdigest() == RUNTIME_RECHECK_SHA256


def assert_recovery_workflow_contract(workflow: str) -> None:
    parsed = parse_workflow(workflow)
    jobs = parse_workflow_steps(workflow)
    assert set(jobs) == EXPECTED_JOBS
    assert "RECOVERY_SOURCE_SHA" not in parsed.get("env", {})

    for job_name, steps in jobs.items():
        checkout_indexes = [
            index
            for index, step in enumerate(steps)
            if str(step.get("uses", "")).startswith("actions/checkout@")
        ]
        verify_indexes = [
            index for index, step in enumerate(steps)
            if step.get("id") == VERIFY_STEP_ID
        ]
        assert checkout_indexes == [0], (
            f"{job_name}: checkout must occur exactly once first"
        )
        assert verify_indexes == [1], (
            f"{job_name}: canonical verification must immediately follow checkout"
        )
        assert steps[0] == {
            "uses": "actions/checkout@v5",
            "with": {"ref": EXPECTED_SHA_EXPRESSION},
        }
        assert_canonical_verify_step(job_name, steps[1])

        seen_rechecks: set[str] = set()
        for index, step in enumerate(steps[2:], start=2):
            uses = step.get("uses")
            assert not str(uses or "").startswith("actions/checkout@"), (
                f"{job_name}: later checkout at step {index}"
            )
            assert not (
                step.get("continue-on-error") is True
                or step.get("if") in {False, "${{ false }}", "false"}
            ), f"{job_name}: security step may be skipped or ignored"
            run = step.get("run")
            if isinstance(run, str):
                for subcommand in git_subcommands(run):
                    assert subcommand in ALLOWED_POST_VERIFY_GIT_SUBCOMMANDS, (
                        f"{job_name}: repository-changing or unknown Git "
                        f"subcommand after verification: {subcommand}"
                    )
                if step.get("id") in RECHECK_IDS:
                    assert_runtime_recheck(job_name, step)
                    seen_rechecks.add(step["id"])
                else:
                    assert "REMEDIATION_CHECKOUT_SHA=" not in run, (
                        f"{job_name}: verified SHA is redefined"
                    )
            env = step.get("env", {})
            assert not (
                isinstance(env, dict) and "REMEDIATION_CHECKOUT_SHA" in env
            ), f"{job_name}: verified SHA is shadowed"
            if str(uses or "").startswith("actions/download-artifact@"):
                path = step.get("with", {}).get("path")
                assert isinstance(path, str) and path.startswith(
                    ".recovery-evidence/"
                ), f"{job_name}: artifact download may overwrite repository root"

        assert seen_rechecks == set(BOUNDARIES[job_name].values())
        for target_name, recheck_id in BOUNDARIES[job_name].items():
            target_index = next(
                index
                for index, step in enumerate(steps)
                if step.get("name") == target_name
            )
            assert target_index > 0
            assert steps[target_index - 1].get("id") == recheck_id, (
                f"{job_name}: {recheck_id} must immediately precede {target_name}"
            )
            assert_runtime_recheck(job_name, steps[target_index - 1])

    recovery = jobs["recovery"]
    producer = step_named(recovery, "Produce recovery execution evidence")
    assert '--source-sha "$REMEDIATION_CHECKOUT_SHA"' in producer["run"]
    assert '--expected-source-sha "$REMEDIATION_CHECKOUT_SHA"' in producer["run"]
    assert '--app-commit "$REMEDIATION_CHECKOUT_SHA"' in producer["run"]
    assert '--workflow-event "$GITHUB_EVENT_NAME"' in producer["run"]
    final = step_named(
        jobs["recovery-evidence"], "Validate exact-SHA recovery evidence"
    )
    assert '--source-sha "$REMEDIATION_CHECKOUT_SHA"' in final["run"]
    assert '--expected-source-sha "$REMEDIATION_CHECKOUT_SHA"' in final["run"]
    assert '--app-commit "$REMEDIATION_CHECKOUT_SHA"' in final["run"]
    assert '--workflow-event "$GITHUB_EVENT_NAME"' in final["run"]
    assert step_named(recovery, "Upload recovery execution evidence")[
        "uses"
    ] == "actions/upload-artifact@v6"
    assert step_named(
        jobs["recovery-evidence"], "Download recovery evidence"
    )["uses"] == "actions/download-artifact@v8"


def mutate_step(
    job: str, name: str, mutator
) -> str:
    parsed = parse_workflow(workflow_text())
    step = step_named(parsed["jobs"][job]["steps"], name)
    mutator(step)
    return dump_workflow(parsed)


def mutate_step_id(job: str, step_id: str, mutator) -> str:
    parsed = parse_workflow(workflow_text())
    matches = [
        step
        for step in parsed["jobs"][job]["steps"]
        if step.get("id") == step_id
    ]
    assert len(matches) == 1
    mutator(matches[0])
    return dump_workflow(parsed)


def test_checked_in_recovery_workflow_satisfies_contract():
    assert_recovery_workflow_contract(workflow_text())


def test_crlf_recovery_workflow_satisfies_contract():
    assert_recovery_workflow_contract(workflow_text().replace("\n", "\r\n"))


@pytest.mark.parametrize(
    "command",
    [
        'git reset --hard HEAD^',
        'git -C "$GITHUB_WORKSPACE" reset --hard HEAD^',
        'cd "$GITHUB_WORKSPACE" && git reset --hard HEAD^',
        'cd "$GITHUB_WORKSPACE"; git reset --hard HEAD^',
        'command git reset --hard HEAD^',
        'env git reset --hard HEAD^',
        'FOO=bar git reset --hard HEAD^',
        'cd "$GITHUB_WORKSPACE"\ngit reset --hard HEAD^',
        'true && git reset --hard HEAD^',
        '(cd "$GITHUB_WORKSPACE" && git reset --hard HEAD^)',
        '{ cd "$GITHUB_WORKSPACE"; git reset --hard HEAD^; }',
        'if true; then git reset --hard HEAD^; fi',
        '/usr/bin/git reset --hard HEAD^',
        'git --git-dir="$GITHUB_WORKSPACE/.git" '
        '--work-tree="$GITHUB_WORKSPACE" reset --hard HEAD^',
        'git -c advice.detachedHead=false reset --hard HEAD^',
        'git update-ref refs/heads/main HEAD^',
        'git read-tree HEAD^',
        'git checkout-index --all',
        'git apply mutation.patch',
        'value="$(git reset --hard HEAD^)"',
    ],
)
def test_post_verify_mutating_git_forms_are_rejected(command: str):
    parsed = parse_workflow(workflow_text())
    steps = parsed["jobs"]["recovery"]["steps"]
    steps.insert(3, {"name": "Mutation", "shell": "bash", "run": command})
    with pytest.raises(AssertionError, match="repository-changing|unknown Git"):
        assert_recovery_workflow_contract(dump_workflow(parsed))


def test_checkout_without_ref_is_rejected():
    parsed = parse_workflow(workflow_text())
    parsed["jobs"]["recovery"]["steps"][0].pop("with")
    with pytest.raises(AssertionError):
        assert_recovery_workflow_contract(dump_workflow(parsed))


def test_pull_request_merge_ref_is_rejected():
    parsed = parse_workflow(workflow_text())
    parsed["jobs"]["recovery"]["steps"][0]["with"]["ref"] = (
        "${{ github.sha }}"
    )
    with pytest.raises(AssertionError):
        assert_recovery_workflow_contract(dump_workflow(parsed))


def test_setup_before_verification_is_rejected():
    parsed = parse_workflow(workflow_text())
    steps = parsed["jobs"]["recovery"]["steps"]
    steps[1], steps[2] = steps[2], steps[1]
    with pytest.raises(AssertionError, match="immediately"):
        assert_recovery_workflow_contract(dump_workflow(parsed))


@pytest.mark.parametrize(
    "run",
    [
        'echo "git rev-parse HEAD ${{ github.sha }} exit 1"',
        CANONICAL_VERIFY_RUN + "true || true\n",
        "set +e\n" + CANONICAL_VERIFY_RUN,
        "ignored='" + CANONICAL_VERIFY_RUN.replace("\n", " ") + "'\necho bypass",
        "verify() {\n" + CANONICAL_VERIFY_RUN + "}\necho bypass",
        "cat <<'VERIFY'\n" + CANONICAL_VERIFY_RUN + "VERIFY\n",
        "exit 0\n" + CANONICAL_VERIFY_RUN,
    ],
)
def test_noncanonical_initial_verification_is_rejected(run: str):
    mutated = mutate_step(
        "recovery",
        "Verify exact source checkout",
        lambda step: step.update(run=run),
    )
    with pytest.raises(AssertionError, match="non-canonical"):
        assert_recovery_workflow_contract(mutated)


def test_continue_on_error_verify_is_rejected():
    mutated = mutate_step(
        "recovery",
        "Verify exact source checkout",
        lambda step: step.update({"continue-on-error": True}),
    )
    with pytest.raises(AssertionError):
        assert_recovery_workflow_contract(mutated)


def test_false_if_verify_is_rejected():
    mutated = mutate_step(
        "recovery",
        "Verify exact source checkout",
        lambda step: step.update({"if": False}),
    )
    with pytest.raises(AssertionError):
        assert_recovery_workflow_contract(mutated)


def test_later_checkout_is_rejected():
    parsed = parse_workflow(workflow_text())
    parsed["jobs"]["recovery"]["steps"].insert(
        4, {"uses": "actions/checkout@v5", "with": {"ref": EXPECTED_SHA_EXPRESSION}}
    )
    with pytest.raises(AssertionError, match="checkout"):
        assert_recovery_workflow_contract(dump_workflow(parsed))


def test_verified_sha_redefinition_is_rejected():
    parsed = parse_workflow(workflow_text())
    parsed["jobs"]["recovery"]["steps"].insert(
        4,
        {
            "name": "Shadow SHA",
            "shell": "bash",
            "run": 'echo "REMEDIATION_CHECKOUT_SHA=deadbeef" >> "$GITHUB_ENV"',
        },
    )
    with pytest.raises(AssertionError, match="redefined"):
        assert_recovery_workflow_contract(dump_workflow(parsed))


def test_independently_declared_evidence_sha_is_rejected():
    mutated = mutate_step(
        "recovery",
        "Produce recovery execution evidence",
        lambda step: step.update(
            run=step["run"].replace(
                '"$REMEDIATION_CHECKOUT_SHA"', '"${{ github.sha }}"'
            )
        ),
    )
    with pytest.raises(AssertionError):
        assert_recovery_workflow_contract(mutated)


def test_missing_or_late_runtime_recheck_is_rejected():
    parsed = parse_workflow(workflow_text())
    steps = parsed["jobs"]["recovery"]["steps"]
    index = next(
        i for i, step in enumerate(steps)
        if step.get("id") == "recheck-source-before-recovery-evidence"
    )
    recheck = steps.pop(index)
    steps.insert(index + 1, recheck)
    with pytest.raises(AssertionError, match="must immediately precede"):
        assert_recovery_workflow_contract(dump_workflow(parsed))


@pytest.mark.parametrize(
    "mutation",
    [
        RUNTIME_RECHECK_RUN + "true || true\n",
        "set +e\n" + RUNTIME_RECHECK_RUN,
        "ignored='" + RUNTIME_RECHECK_RUN.replace("\n", " ") + "'\necho bypass",
    ],
)
def test_noncanonical_runtime_recheck_is_rejected(mutation: str):
    mutated = mutate_step_id(
        "recovery",
        "recheck-source-before-recovery-evidence",
        lambda step: step.update(run=mutation),
    )
    with pytest.raises(AssertionError, match="non-canonical"):
        assert_recovery_workflow_contract(mutated)


def test_download_to_repository_root_is_rejected():
    mutated = mutate_step(
        "recovery-evidence",
        "Download recovery evidence",
        lambda step: step["with"].update(path="."),
    )
    with pytest.raises(AssertionError, match="overwrite repository root"):
        assert_recovery_workflow_contract(mutated)


def run_recheck(repo: Path, expected: str, marker: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(
        {
            "REMEDIATION_CHECKOUT_SHA": expected,
            "GITHUB_WORKSPACE": subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
                text=True,
            ).strip(),
            "GITHUB_ENV": str(repo / "github-env.txt"),
        }
    )
    script = RUNTIME_RECHECK_RUN + f'\nprintf ok > "{marker.as_posix()}"\n'
    return subprocess.run(
        [str(GIT_BASH), "-c", script],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.fixture
def two_commit_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    tracked = repo / "tracked.txt"
    tracked.write_text("first\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "first"], check=True)
    tracked.write_text("second\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "commit", "-qam", "second"], check=True)
    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    return repo, head


def test_runtime_recheck_allows_clean_verified_repository(
    two_commit_repo: tuple[Path, str],
):
    repo, expected = two_commit_repo
    marker = repo.parent / "evidence-marker"
    result = run_recheck(repo, expected, marker)
    assert result.returncode == 0, result.stderr
    assert marker.is_file()


@pytest.mark.parametrize("form", ["git-c", "cd-and"])
def test_runtime_recheck_rejects_head_mutation(
    two_commit_repo: tuple[Path, str], form: str
):
    repo, expected = two_commit_repo
    if form == "git-c":
        command = ["git", "-C", str(repo), "reset", "--hard", "HEAD^"]
    else:
        command = [
            str(GIT_BASH),
            "-c",
            f'cd "{repo.as_posix()}" && git reset --hard HEAD^',
        ]
    subprocess.run(command, check=True, capture_output=True)
    marker = repo.parent / f"evidence-{form}"
    result = run_recheck(repo, expected, marker)
    assert result.returncode != 0
    assert not marker.exists()


@pytest.mark.parametrize("staged", [False, True])
def test_runtime_recheck_rejects_tracked_or_index_drift(
    two_commit_repo: tuple[Path, str], staged: bool
):
    repo, expected = two_commit_repo
    (repo / "tracked.txt").write_text("mutated\n", encoding="utf-8")
    if staged:
        subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    marker = repo.parent / f"evidence-drift-{staged}"
    result = run_recheck(repo, expected, marker)
    assert result.returncode != 0
    assert not marker.exists()


def test_runtime_recheck_rejects_active_git_operation(
    two_commit_repo: tuple[Path, str],
):
    repo, expected = two_commit_repo
    git_dir = Path(
        subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "--git-dir"], text=True
        ).strip()
    )
    if not git_dir.is_absolute():
        git_dir = repo / git_dir
    (git_dir / "MERGE_HEAD").write_text("0" * 40 + "\n", encoding="ascii")
    marker = repo.parent / "evidence-active-operation"
    result = run_recheck(repo, expected, marker)
    assert result.returncode != 0
    assert not marker.exists()
