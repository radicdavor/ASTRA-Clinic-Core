from __future__ import annotations

import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_CODEOWNERS = {"@radicdavor"}
NATIVE_DEV_TEST_PATH = "scripts/tests/test_native_dev.py"
NATIVE_DEV_NODE_IDS = {
    f"{NATIVE_DEV_TEST_PATH}::test_resolved_identity_percent_encodes_without_leaking",
    *{
        f"{NATIVE_DEV_TEST_PATH}::test_resolved_identity_rejects_unsafe_config[bad{index}]"
        for index in range(5)
    },
    *{
        f"{NATIVE_DEV_TEST_PATH}::test_database_url_rejects_target_overrides[{host}]"
        for host in ("remote", "db,remote", "127.0.0.1?host=remote")
    },
    f"{NATIVE_DEV_TEST_PATH}::test_seed_keeps_database_url_out_of_command_line",
}


@dataclass(frozen=True)
class ReadmeMutationCase:
    case_id: str
    target_invariant: str
    mutate_readme: Callable[[str], str]
    mutate_gitignore: Callable[[str], str] = lambda text: text


README_MUTATION_CASES = (
    ReadmeMutationCase(
        "mode-full-compose-in-native",
        "mode_separation",
        lambda text: text.replace(
            "### Option B: native backend with Compose PostgreSQL",
            "### Option B: native backend with Compose PostgreSQL"
            "\n\n```bash\ndocker compose up --build\n```",
        ),
    ),
    ReadmeMutationCase(
        "db-service-unbounded-up",
        "db_only",
        lambda text: text.replace("docker compose up -d db", "docker compose up -d"),
    ),
    ReadmeMutationCase(
        "db-service-backend-up",
        "db_only",
        lambda text: text.replace(
            "docker compose up -d db", "docker compose up -d backend"
        ),
    ),
    ReadmeMutationCase(
        "storage-container-path",
        "storage",
        lambda text: text.replace(".astra-dev/documents", "/app/data/documents"),
    ),
    ReadmeMutationCase(
        "storage-unignored-root",
        "storage",
        lambda text: text,
        lambda text: text.replace(".astra-dev/", ""),
    ),
    ReadmeMutationCase(
        "port-native-8001",
        "port",
        lambda text: text.replace(
            "native Uvicorn on port `8000`", "native Uvicorn on port `8001`"
        ),
    ),
    ReadmeMutationCase(
        "environment-real-data-authorized",
        "environment",
        lambda text: text.replace(
            "Neither mode\nauthorizes deployment, production use, or real patient data",
            "Neither mode\nauthorizes deployment or production use; real patient data is allowed",
        ),
    ),
    ReadmeMutationCase(
        "ordering-seed-after-serve",
        "ordering",
        lambda text: text.replace(
            "python scripts/native_dev.py seed\npython scripts/native_dev.py serve",
            "python scripts/native_dev.py serve\npython scripts/native_dev.py seed",
        ),
    ),
    ReadmeMutationCase(
        "ssot-execute-dotenv",
        "ssot",
        lambda text: text.replace(
            "instead of executing `.env`", "by executing `.env` as shell code"
        ),
    ),
    ReadmeMutationCase(
        "readiness-claims-demo-users",
        "readiness",
        lambda text: text.replace(
            "they do not prove\nthat demo users exist", "they prove that demo users exist"
        ),
    ),
    ReadmeMutationCase(
        "shell-bash-labelled-powershell",
        "shells",
        lambda text: text.replace(
            "Linux/bash:\n\n```bash", "Linux/bash:\n\n```powershell", 1
        ),
    ),
)


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _load_yaml(path: Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)


def _assert_native_dev_ci_contract(workflow: dict) -> None:
    events = workflow.get("on", workflow.get(True))
    assert isinstance(events, dict)
    assert {"push", "pull_request"} <= set(events)
    required_paths = {
        "scripts/native_dev.py",
        NATIVE_DEV_TEST_PATH,
        ".github/workflows/ci.yml",
        "scripts/tests/test_repository_governance.py",
    }
    for event in ("push", "pull_request"):
        event_config = events[event]
        if isinstance(event_config, dict) and "paths" in event_config:
            assert required_paths <= set(event_config["paths"])

    backend = workflow["jobs"]["backend"]
    assert backend.get("name", "backend") == "backend"
    steps = backend["steps"]
    test_steps = [step for step in steps if step.get("name") == "Test remediation evidence validator"]
    assert len(test_steps) == 1
    step = test_steps[0]
    assert "if" not in step and not step.get("continue-on-error", False)
    assert step.get("working-directory", ".") in (".", "${{ github.workspace }}")

    raw_command = step.get("run", "")
    assert not any(token in raw_command for token in ("&&", "||", ";", "exit ", "if "))
    assert not any(line.lstrip().startswith("#") for line in raw_command.splitlines())
    command = re.sub(r"\\\s*\n", " ", raw_command)
    tokens = shlex.split(command, posix=True)
    assert tokens[:3] == ["python", "-m", "pytest"]
    pytest_arguments = tokens[3:]
    assert NATIVE_DEV_TEST_PATH in tokens
    assert tokens.count(NATIVE_DEV_TEST_PATH) == 1
    assert not any(
        token == "-k" or token.startswith("-k=") for token in pytest_arguments
    )
    assert not any(
        token == "-m" or token.startswith("-m=") for token in pytest_arguments
    )
    assert not any(
        token == "--ignore" or token.startswith("--ignore=")
        for token in pytest_arguments
    )


def _collect_native_dev_node_ids() -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", NATIVE_DEV_TEST_PATH, "--collect-only", "-q"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.startswith(f"{NATIVE_DEV_TEST_PATH}::")
    ]


def _relative_links(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [
        match.group(1).split("#", 1)[0]
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text)
        if match.group(1)
        and not match.group(1).startswith(("http://", "https://", "mailto:", "#"))
    ]


def _markdown_code_blocks(path: Path) -> list[tuple[str, ...]]:
    return _markdown_code_blocks_from_text(path.read_text(encoding="utf-8"))


def _assert_private_reporting_consistency(documents: dict[str, str]) -> None:
    normalized = {
        name: " ".join(text.lower().split()) for name, text in documents.items()
    }
    combined = "\n".join(normalized.values())
    forbidden_stale_claims = (
        "private vulnerability reporting is not currently enabled",
        "private vulnerability-reporting channel is not currently configured",
        "no verified private reporting channel",
    )
    for claim in forbidden_stale_claims:
        assert claim not in combined, f"stale private-reporting claim: {claim}"

    contributing = normalized["CONTRIBUTING.md"]
    assert "[`security.md`](security.md)" in contributing, (
        "CONTRIBUTING.md must link to the canonical security policy"
    )
    assert "private github security advisory flow" in contributing, (
        "CONTRIBUTING.md must direct sensitive reports to the private flow"
    )
    assert "never place sensitive vulnerability details in a public issue" in contributing
    assert "does not prove response ownership" in contributing, (
        "channel availability must not claim operational completion"
    )
    assert "response ownership" in combined and "sla" in combined
    assert "exercised" in combined and "intake" in combined


def _assert_database_guidance(
    readme: str, compose: dict, gitignore: str, entrypoint: str
) -> None:
    assert "### Option A: full Compose stack" in readme
    assert "### Option B: native backend with Compose PostgreSQL" in readme
    full = readme.split("### Option A: full Compose stack", 1)[1].split(
        "### Option B: native backend with Compose PostgreSQL", 1
    )[0]
    native = readme.split(
        "### Option B: native backend with Compose PostgreSQL", 1
    )[1].split("## Frontend development", 1)[0]
    full_blocks = _markdown_fenced_blocks_from_text(full)
    native_blocks = _markdown_fenced_blocks_from_text(native)
    full_commands = {
        line for _, block in full_blocks for line in block if line
    }
    native_commands = {
        line for _, block in native_blocks for line in block if line
    }
    invariants = _database_guidance_invariants(readme, gitignore)
    for invariant, valid in invariants.items():
        assert valid, f"README native {invariant} contract failed"
    services = compose["services"]

    assert {"db", "backend"} <= set(services), "Compose DB/backend services are required"
    assert "127.0.0.1:5432:5432" in services["db"]["ports"], (
        "native-host guidance requires the loopback PostgreSQL port"
    )
    assert "docker compose up --build" in full_commands
    assert not any("uvicorn" in line for line in full_commands)
    assert "alternatives" in readme.lower()
    assert "docker compose up -d db" in native_commands
    assert not any(
        re.fullmatch(r"docker compose up(?:\s+-d)?", line)
        or line == "docker compose up --build"
        for line in native_commands
    ), "native mode must start only the DB service"
    assert "docker compose up -d backend" not in native_commands
    seed_command = "python scripts/native_dev.py seed"
    assert not any(
        "alembic upgrade head" in block and "cd backend" in block
        for _, block in native_blocks
    ), "migration guidance must not mix host cwd and container DNS"

    uvicorn_blocks = [
        (language, block)
        for language, block in native_blocks
        if any("native_dev.py serve" in line for line in block)
    ]
    assert {language for language, _ in uvicorn_blocks} == {"bash", "powershell"}
    assert len(uvicorn_blocks) == 2, "README must define bash and PowerShell host blocks"
    for language, block in uvicorn_blocks:
        joined = "\n".join(block)
        assert "DATABASE_URL=" not in joined and "@db:" not in joined
        assert "cd backend" not in block
        assert "python scripts/native_dev.py serve" in joined
        if language == "bash":
            assert "$env:" not in joined and "New-Item" not in joined
        else:
            assert "export " not in joined and "$(pwd)" not in joined
    assert "`docker compose down`" in native
    assert "instead of executing `.env`" in native
    assert "they do not prove\nthat demo users exist" in native
    assert "successful synthetic login is not evidence of production readiness" in native
    assert "never run the demo seed against a production database" in native.lower()
    _assert_entrypoint_sequence(entrypoint)


def _database_guidance_invariants(readme: str, gitignore: str) -> dict[str, bool]:
    native_heading = "### Option B: native backend with Compose PostgreSQL"
    if native_heading not in readme or "## Frontend development" not in readme:
        return {
            name: False
            for name in (
                "mode_separation",
                "db_only",
                "storage",
                "port",
                "environment",
                "seed",
                "ordering",
                "ssot",
                "readiness",
                "shells",
            )
        }
    native = readme.split(native_heading, 1)[1].split("## Frontend development", 1)[0]
    native_blocks = _markdown_fenced_blocks_from_text(native)
    native_commands = {line for _, block in native_blocks for line in block if line}
    serve_blocks = [
        block
        for _, block in native_blocks
        if any("native_dev.py serve" in line for line in block)
    ]
    seed_command = "python scripts/native_dev.py seed"
    serve_command = "python scripts/native_dev.py serve"
    seed_present = bool(serve_blocks) and all(seed_command in block for block in serve_blocks)
    ordering_valid = seed_present and all(
        block.index(seed_command) < block.index(serve_command) for block in serve_blocks
    )
    joined_serve_blocks = "\n".join("\n".join(block) for block in serve_blocks)
    return {
        "mode_separation": (
            "This is an alternative to Option A" in native
            and "docker compose up --build" not in native_commands
        ),
        "db_only": (
            "docker compose up -d db" in native_commands
            and "docker compose up -d backend" not in native_commands
            and not any(
                re.fullmatch(r"docker compose up(?:\s+-d)?", line)
                for line in native_commands
            )
        ),
        "storage": (
            "`.astra-dev/documents` directory" in native
            and ".astra-dev/" in gitignore.splitlines()
            and "/app/data/documents" not in joined_serve_blocks
        ),
        "port": (
            "native Uvicorn on port `8000`" in native
            and "native Uvicorn on port `8001`" not in native
        ),
        "environment": (
            "Never run the demo seed against a production database" in native
            and "Neither mode\nauthorizes deployment, production use, or real patient data"
            in native
        ),
        "seed": seed_present,
        "ordering": ordering_valid,
        "ssot": "instead of executing `.env`" in native,
        "readiness": "they do not prove\nthat demo users exist" in native,
        "shells": (
            {
                language
                for language, block in native_blocks
                if any("native_dev.py serve" in line for line in block)
            }
            == {"bash", "powershell"}
        ),
    }


def _evaluate_readme_mutant(
    case: ReadmeMutationCase,
    canonical: str,
    canonical_gitignore: str,
) -> dict[str, object]:
    mutated = case.mutate_readme(canonical)
    mutated_gitignore = case.mutate_gitignore(canonical_gitignore)
    content_changed = (mutated, mutated_gitignore) != (canonical, canonical_gitignore)
    semantic_changed = (
        "".join(mutated.split()), "".join(mutated_gitignore.split())
    ) != ("".join(canonical.split()), "".join(canonical_gitignore.split()))
    invariants = _database_guidance_invariants(mutated, mutated_gitignore)
    target_failed = not invariants[case.target_invariant]
    unrelated_failed = sorted(
        name
        for name, valid in invariants.items()
        if name != case.target_invariant and not valid
    )
    full_validator_failed = False
    failure = ""
    try:
        _assert_database_guidance(
            mutated,
            _load_yaml(ROOT / "docker-compose.yml"),
            mutated_gitignore,
            (ROOT / "backend/entrypoint.sh").read_text(encoding="utf-8"),
        )
    except AssertionError as exc:
        full_validator_failed = True
        failure = str(exc)
    return {
        "case_id": case.case_id,
        "target_invariant": case.target_invariant,
        "content_changed": content_changed,
        "semantic_changed": semantic_changed,
        "target_failed": target_failed,
        "unrelated_failed": unrelated_failed,
        "full_validator_failed": full_validator_failed,
        "failure_attributed_to_target": (
            content_changed
            and target_failed
            and not unrelated_failed
            and full_validator_failed
            and case.target_invariant in failure
        ),
        "mutant": (mutated, mutated_gitignore),
    }


def _assert_entrypoint_sequence(entrypoint: str) -> None:
    executable = [
        line.strip()
        for line in entrypoint.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    canonical = ("alembic upgrade head", "python -m app.seed", "python -m app.demo.seed")
    positions = [executable.index(command) for command in canonical]
    assert positions == sorted(positions)
    assert executable[-1] == 'exec "$@"'


def _assert_entrypoint_file_contract(
    attributes: str, content: bytes, mode: str, dockerfile: str
) -> None:
    rules = {
        line.strip()
        for line in attributes.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "backend/entrypoint.sh text eol=lf" in rules
    assert b"\r\n" not in content
    assert not content.startswith(b"\xef\xbb\xbf")
    assert content.startswith(b"#!/bin/sh\n")
    assert mode == "100644"
    assert "RUN chmod +x /app/entrypoint.sh" in dockerfile


def _markdown_code_blocks_from_text(text: str) -> list[tuple[str, ...]]:
    return [block for _, block in _markdown_fenced_blocks_from_text(text)]


def _markdown_fenced_blocks_from_text(
    text: str,
) -> list[tuple[str, tuple[str, ...]]]:
    blocks: list[tuple[str, tuple[str, ...]]] = []
    current: list[str] | None = None
    language = ""
    for line in text.splitlines():
        if line.startswith("```"):
            if current is None:
                current = []
                language = line[3:].strip().lower()
            else:
                blocks.append((language, tuple(current)))
                current = None
        elif current is not None:
            current.append(line.strip())
    assert current is None, "unclosed Markdown code block"
    return blocks


RPO_RTO_TARGETS = (
    "RPO 24 h (maximum 24 h), RTO 2 h (maximum 4 h)",
    "RPO 4 h (maximum 8 h), RTO 2 h (maximum 4 h)",
    "RPO 15 min (maximum 1 h), RTO 2 h (maximum 4 h)",
)


def _assert_rpo_rto_consistency(documents: dict[str, str]) -> None:
    recovery = " ".join(documents["recovery"].split())
    limitations = " ".join(documents["limitations"].split())
    backlog = " ".join(documents["backlog"].split())
    combined = "\n".join((recovery, limitations, backlog)).lower()

    for target in RPO_RTO_TARGETS:
        assert target in recovery, f"missing accepted RPO/RTO target: {target}"
    assert "Owner acceptance of these policy targets: `true` (accepted 2026-07-30)" in recovery
    assert "Observed production RPO: not measured (`null`)" in recovery
    assert "Observed production RTO: not measured (`null`)" in recovery
    assert "accepted the [recovery contract](recovery-contract-0071.md) RPO/RTO policy targets on 2026-07-30" in limitations
    assert "observed production RPO and RTO remain `null`" in limitations
    assert "Policy targets accepted by the owner on 2026-07-30; observed values are `null`" in backlog
    assert "rpo/rto and operator drills are not approved" not in combined
    assert "production recovery: not authorized" in combined
    assert "no row in this backlog is currently `production_authorized`" in combined


@pytest.mark.parametrize(
    "path",
    sorted((ROOT / ".github").rglob("*.yml"))
    + sorted((ROOT / ".github").rglob("*.yaml")),
)
def test_github_yaml_is_safe_and_has_unique_keys(path: Path) -> None:
    assert _load_yaml(path) is not None


def test_duplicate_yaml_keys_are_rejected() -> None:
    with pytest.raises(yaml.constructor.ConstructorError, match="duplicate key"):
        yaml.load("version: 2\nversion: 3\n", Loader=UniqueKeyLoader)


def test_ci_collects_native_development_safety_contract() -> None:
    workflow = _load_yaml(ROOT / ".github/workflows/ci.yml")
    _assert_native_dev_ci_contract(workflow)
    node_ids = _collect_native_dev_node_ids()
    assert len(node_ids) == len(set(node_ids)), "native-dev collection has duplicates"
    assert set(node_ids) == NATIVE_DEV_NODE_IDS


@pytest.mark.parametrize(
    "mutation",
    (
        "remove-target",
        "typo-target",
        "ignore-target",
        "deselect-k",
        "exclude-marker",
        "comment-only",
        "step-name-only",
        "dead-branch",
        "noop",
        "push-only",
        "pull-request-only",
        "rename-check",
        "missing-native-path-filter",
        "missing-test-path-filter",
    ),
)
def test_native_development_ci_contract_rejects_mutations(mutation: str) -> None:
    workflow = _load_yaml(ROOT / ".github/workflows/ci.yml")
    events = workflow.get("on", workflow.get(True))
    backend = workflow["jobs"]["backend"]
    step = next(
        item
        for item in backend["steps"]
        if item.get("name") == "Test remediation evidence validator"
    )
    if mutation == "remove-target":
        step["run"] = step["run"].replace(f"{NATIVE_DEV_TEST_PATH} \\\n", "")
    elif mutation == "typo-target":
        step["run"] = step["run"].replace(NATIVE_DEV_TEST_PATH, "scripts/tests/test_native_de.py")
    elif mutation == "ignore-target":
        step["run"] += f" --ignore={NATIVE_DEV_TEST_PATH}"
    elif mutation == "deselect-k":
        step["run"] += " -k 'not native_dev'"
    elif mutation == "exclude-marker":
        step["run"] += " -m 'not native_dev'"
    elif mutation == "comment-only":
        step["run"] = "# " + NATIVE_DEV_TEST_PATH + "\npython -m pytest scripts/tests/test_repository_governance.py -q"
    elif mutation == "step-name-only":
        step["name"] += f" {NATIVE_DEV_TEST_PATH}"
        step["run"] = step["run"].replace(NATIVE_DEV_TEST_PATH, "")
    elif mutation == "dead-branch":
        step["run"] = "exit 0\n" + step["run"]
    elif mutation == "noop":
        step["run"] = f"echo {NATIVE_DEV_TEST_PATH}"
    elif mutation == "push-only":
        events.pop("pull_request")
    elif mutation == "pull-request-only":
        events.pop("push")
    elif mutation == "rename-check":
        backend["name"] = "backend-renamed"
    elif mutation == "missing-native-path-filter":
        events["push"] = {"paths": [NATIVE_DEV_TEST_PATH, ".github/workflows/ci.yml", "scripts/tests/test_repository_governance.py"]}
    elif mutation == "missing-test-path-filter":
        events["pull_request"] = {"paths": ["scripts/native_dev.py", ".github/workflows/ci.yml", "scripts/tests/test_repository_governance.py"]}
    with pytest.raises((AssertionError, KeyError, ValueError)):
        _assert_native_dev_ci_contract(workflow)


@pytest.mark.parametrize(
    "node_ids",
    (
        [],
        sorted(NATIVE_DEV_NODE_IDS)[:-1],
        [*sorted(NATIVE_DEV_NODE_IDS), sorted(NATIVE_DEV_NODE_IDS)[0]],
    ),
)
def test_native_development_collection_rejects_incomplete_or_duplicate_nodes(
    node_ids: list[str],
) -> None:
    with pytest.raises(AssertionError):
        assert len(node_ids) == len(set(node_ids)) and set(node_ids) == NATIVE_DEV_NODE_IDS


def test_codeowners_uses_only_known_owner_identities() -> None:
    path = ROOT / ".github" / "CODEOWNERS"
    lines = [
        line.split()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert lines
    assert lines[0] == ["*", "@radicdavor"]
    owners = {owner for fields in lines for owner in fields[1:]}
    assert owners == ALLOWED_CODEOWNERS
    assert all(fields[0].startswith(("*", "/")) for fields in lines)


@pytest.mark.parametrize("document", [ROOT / "README.md", ROOT / "docs" / "README.md"])
def test_entrypoint_internal_links_exist(document: Path) -> None:
    missing = [
        link
        for link in _relative_links(document)
        if not (document.parent / link).resolve().exists()
    ]
    assert missing == []


def test_readme_is_a_bounded_current_entrypoint() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    assert 150 <= len(lines) <= 300
    assert text.count("](docs/") <= 15
    assert "controlled synthetic demo" in text.lower()
    assert "do not enter real patient" in text.lower()
    assert "Apache License 2.0" in text
    assert "production" in text and "real patient data" in text


def test_current_docs_use_executable_root_relative_fast_gate() -> None:
    documents = [ROOT / "README.md", ROOT / "docs" / "test-strategy.md"]
    blocks = [block for document in documents for block in _markdown_code_blocks(document)]
    commands = {line for block in blocks for line in block if line and not line.startswith("#")}

    assert "python scripts/run_test_gate.py fast" in commands
    assert "python -m pytest backend/tests -q" not in commands
    assert not any(
        "cd backend" in block and "python scripts/run_test_gate.py fast" in block
        for block in blocks
    )
    assert (ROOT / "scripts" / "run_test_gate.py").is_file()


def test_readme_database_guidance_has_one_execution_context() -> None:
    _assert_database_guidance(
        (ROOT / "README.md").read_text(encoding="utf-8"),
        _load_yaml(ROOT / "docker-compose.yml"),
        (ROOT / ".gitignore").read_text(encoding="utf-8"),
        (ROOT / "backend/entrypoint.sh").read_text(encoding="utf-8"),
    )


def test_entrypoint_has_portable_lf_and_executable_image_contract() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    mode = subprocess.run(
        ["git", "ls-files", "-s", "backend/entrypoint.sh"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()[0]
    _assert_entrypoint_file_contract(
        attributes,
        (ROOT / "backend/entrypoint.sh").read_bytes(),
        mode,
        (ROOT / "backend/Dockerfile").read_text(encoding="utf-8"),
    )
    result = subprocess.run(
        ["git", "check-attr", "text", "eol", "--", "backend/entrypoint.sh"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "text: set" in result and "eol: lf" in result


@pytest.mark.parametrize(
    ("attributes", "content", "mode", "dockerfile"),
    (
        ("", b"#!/bin/sh\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=crlf\n", b"#!/bin/sh\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=native\n", b"#!/bin/sh\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.s text eol=lf\n", b"#!/bin/sh\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=lf\n", b"#!/bin/sh\r\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=lf\n", b"\xef\xbb\xbf#!/bin/sh\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=lf\n", b"#!/usr/bin/missing\n", "100644", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=lf\n", b"#!/bin/sh\n", "100755", "RUN chmod +x /app/entrypoint.sh"),
        ("backend/entrypoint.sh text eol=lf\n", b"#!/bin/sh\n", "100644", ""),
    ),
)
def test_entrypoint_file_contract_rejects_mutations(
    attributes: str, content: bytes, mode: str, dockerfile: str
) -> None:
    with pytest.raises(AssertionError):
        _assert_entrypoint_file_contract(attributes, content, mode, dockerfile)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda text: text.replace("  python -m app.seed\n", ""),
        lambda text: text.replace("    python -m app.demo.seed\n", ""),
        lambda text: text.replace(
            "  alembic upgrade head\n  python -m app.seed",
            "  python -m app.seed\n  alembic upgrade head",
        ),
        lambda text: text.replace(
            "    python -m app.demo.seed\n  fi",
            "  fi\n  exec \"$@\"\n  # python -m app.demo.seed",
        ),
    ),
)
def test_entrypoint_sequence_rejects_mutations(mutation) -> None:
    entrypoint = (ROOT / "backend/entrypoint.sh").read_text(encoding="utf-8")
    with pytest.raises((AssertionError, ValueError)):
        _assert_entrypoint_sequence(mutation(entrypoint))


def test_readme_database_guidance_baseline() -> None:
    _assert_database_guidance(
        (ROOT / "README.md").read_text(encoding="utf-8"),
        _load_yaml(ROOT / "docker-compose.yml"),
        (ROOT / ".gitignore").read_text(encoding="utf-8"),
        (ROOT / "backend/entrypoint.sh").read_text(encoding="utf-8"),
    )


@pytest.mark.parametrize("case", README_MUTATION_CASES, ids=lambda case: case.case_id)
def test_readme_database_guidance_rejects_single_fault_mutations(case) -> None:
    result = _evaluate_readme_mutant(
        case,
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (ROOT / ".gitignore").read_text(encoding="utf-8"),
    )
    assert result["content_changed"], f"{case.case_id} was an ineffective mutation"
    assert result["semantic_changed"], f"{case.case_id} changed only whitespace"
    assert result["target_failed"], f"{case.case_id} did not break {case.target_invariant}"
    assert result["unrelated_failed"] == [], (
        f"{case.case_id} also broke {result['unrelated_failed']}"
    )
    assert result["full_validator_failed"]
    assert result["failure_attributed_to_target"]


def test_readme_mutation_noop_control_is_not_a_killed_mutant() -> None:
    canonical = (ROOT / "README.md").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    result = _evaluate_readme_mutant(
        ReadmeMutationCase("noop-storage", "storage", lambda text: text),
        canonical,
        gitignore,
    )
    assert result["content_changed"] is False
    assert result["semantic_changed"] is False
    assert result["target_failed"] is False
    assert result["full_validator_failed"] is False
    assert result["failure_attributed_to_target"] is False


def test_readme_mutation_matrix_has_unique_effective_outputs() -> None:
    canonical = (ROOT / "README.md").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    results = [
        _evaluate_readme_mutant(case, canonical, gitignore)
        for case in README_MUTATION_CASES
    ]
    case_ids = [case.case_id for case in README_MUTATION_CASES]
    outputs = [result["mutant"] for result in results]
    assert len(case_ids) == len(set(case_ids))
    assert len(outputs) == len(set(outputs))
    assert all(result["content_changed"] for result in results)
    assert all(result["semantic_changed"] for result in results)
    assert all(case.target_invariant for case in README_MUTATION_CASES)


def test_readme_mutation_harness_rejects_compound_faults() -> None:
    canonical = (ROOT / "README.md").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    compound = ReadmeMutationCase(
        "compound-storage-seed",
        "storage",
        lambda text: text.replace(".astra-dev/documents", "/app/data/documents").replace(
            "python scripts/native_dev.py seed", ""
        ),
    )
    result = _evaluate_readme_mutant(compound, canonical, gitignore)
    assert result["content_changed"] is True
    assert result["target_failed"] is True
    assert result["unrelated_failed"] == ["ordering", "seed"]
    assert result["full_validator_failed"] is True
    assert result["failure_attributed_to_target"] is False


def test_old_common_seed_kill_switch_cannot_claim_targeted_coverage() -> None:
    canonical = (ROOT / "README.md").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    legacy_coupled = ReadmeMutationCase(
        "legacy-noop-storage-plus-seed-removal",
        "storage",
        lambda text: text.replace("obsolete storage command", "replacement").replace(
            "python scripts/native_dev.py seed", ""
        ),
    )
    result = _evaluate_readme_mutant(legacy_coupled, canonical, gitignore)
    assert result["content_changed"] is True
    assert result["target_failed"] is False
    assert result["unrelated_failed"] == ["ordering", "seed"]
    assert result["full_validator_failed"] is True
    assert result["failure_attributed_to_target"] is False


def test_canonical_rpo_rto_documents_are_consistent() -> None:
    _assert_rpo_rto_consistency(
        {
            "recovery": (ROOT / "docs/recovery-contract-0071.md").read_text(
                encoding="utf-8"
            ),
            "limitations": (
                ROOT / "docs/CURRENT_OPERATIONAL_LIMITATIONS.md"
            ).read_text(encoding="utf-8"),
            "backlog": (
                ROOT / "docs/PRODUCTION_READINESS_BACKLOG.md"
            ).read_text(encoding="utf-8"),
        }
    )


@pytest.mark.parametrize(
    ("document", "old", "new"),
    (
        ("recovery", "RPO 15 min", "RPO 30 min"),
        ("recovery", "policy targets: `true`", "policy targets: `false`"),
        ("recovery", "not measured (`null`)", "measured (`15 min`)"),
        ("backlog", "observed values are `null`", "production readiness is proven"),
        (
            "limitations",
            "accepted the [recovery contract]",
            "has not approved the [recovery contract]",
        ),
    ),
)
def test_rpo_rto_consistency_rejects_mutations(
    document: str, old: str, new: str
) -> None:
    documents = {
        "recovery": (ROOT / "docs/recovery-contract-0071.md").read_text(
            encoding="utf-8"
        ),
        "limitations": (ROOT / "docs/CURRENT_OPERATIONAL_LIMITATIONS.md").read_text(
            encoding="utf-8"
        ),
        "backlog": (ROOT / "docs/PRODUCTION_READINESS_BACKLOG.md").read_text(
            encoding="utf-8"
        ),
    }
    assert old in documents[document]
    documents[document] = documents[document].replace(old, new, 1)
    with pytest.raises(AssertionError):
        _assert_rpo_rto_consistency(documents)


def test_apache_license_is_canonical_and_linked() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "Grant of Patent License" in license_text
    assert "END OF TERMS AND CONDITIONS" in license_text
    assert "[Apache License 2.0](LICENSE)" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )


def test_license_decision_matches_canonical_apache_license() -> None:
    decision = (ROOT / "docs" / "LICENSE_DECISION.md").read_text(encoding="utf-8")
    normalized_decision = " ".join(decision.lower().split())
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "selected the **Apache License 2.0**" in decision
    assert "[`LICENSE`](../LICENSE) file is the authoritative license text" in decision
    assert "No final open-source license has been selected" not in decision
    assert "[License decision](LICENSE_DECISION.md)" in index
    for boundary in ("deployment", "production", "real patient data"):
        assert boundary in normalized_decision


def test_private_vulnerability_reporting_documents_are_consistent() -> None:
    documents = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "README.md",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "docs/PRODUCTION_READINESS_BACKLOG.md",
            "docs/README.md",
        )
    }
    security = documents["SECURITY.md"]
    readme = documents["README.md"]
    normalized_readme = " ".join(readme.lower().split())
    backlog = documents["docs/PRODUCTION_READINESS_BACKLOG.md"]
    advisory_url = (
        "https://github.com/radicdavor/ASTRA-Clinic-Core/security/advisories/new"
    )
    assert advisory_url in security
    assert "private vulnerability reporting is enabled" in security.lower()
    assert "private vulnerability reporting is enabled" in normalized_readme
    assert "not currently configured" not in readme
    assert "not currently enabled" not in security
    vulnerability_row = next(
        line for line in backlog.splitlines() if line.startswith("| Vulnerability disclosure")
    )
    assert "GitHub private vulnerability reporting enabled" in vulnerability_row
    assert "response ownership" in vulnerability_row
    assert vulnerability_row.endswith("| DESIGNED |")
    _assert_private_reporting_consistency(documents)


@pytest.mark.parametrize(
    ("replacement", "message"),
    [
        (
            "No verified private reporting channel is configured.",
            "stale private-reporting claim",
        ),
        ("Submit sensitive reports privately.", "canonical security policy"),
        (
            "[`SECURITY.md`](SECURITY.md) proves the response process is complete.",
            "private flow",
        ),
    ],
)
def test_private_reporting_consistency_rejects_mutations(
    replacement: str, message: str
) -> None:
    documents = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "README.md",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "docs/PRODUCTION_READINESS_BACKLOG.md",
            "docs/README.md",
        )
    }
    documents["CONTRIBUTING.md"] = replacement
    with pytest.raises(AssertionError, match=message):
        _assert_private_reporting_consistency(documents)


def test_documentation_index_has_unambiguous_categories() -> None:
    text = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    required = {
        "## Canonical current state",
        "## Architecture and ADRs",
        "## Security and privacy",
        "## Operations and recovery",
        "## Testing and release",
        "## Current program decisions",
        "## Historical implementation evidence",
    }
    assert required <= set(text.splitlines())
    assert "does not automatically prove the current runtime" in text


def test_readiness_decisions_remain_separate() -> None:
    documents = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ["README.md", "CONTRIBUTING.md", "docs/PRODUCTION_READINESS_BACKLOG.md"]
    ).lower()
    for decision in ("merge", "deployment", "production", "real patient data"):
        assert decision in documents
    assert "no row in this backlog is currently `production_authorized`" in documents


def test_dependabot_covers_real_ecosystems_without_automerge() -> None:
    path = ROOT / ".github" / "dependabot.yml"
    raw = path.read_text(encoding="utf-8")
    config = _load_yaml(path)
    updates = config["updates"]
    actual = {(entry["package-ecosystem"], entry["directory"]) for entry in updates}
    assert actual == {("npm", "/frontend"), ("pip", "/backend"), ("pip", "/scripts"), ("github-actions", "/")}
    assert (ROOT / "frontend").is_dir() and (ROOT / "backend").is_dir()
    assert all(entry["open-pull-requests-limit"] <= 5 for entry in updates)
    assert all(entry["schedule"]["interval"] == "weekly" for entry in updates)
    assert "automerge" not in raw.lower()
    assert (ROOT / "scripts" / "test-requirements.txt").is_file()
