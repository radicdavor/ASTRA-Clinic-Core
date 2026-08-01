from __future__ import annotations

import ast
import copy
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote, unquote

import pytest
import yaml
from sqlalchemy.engine import make_url


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_CODEOWNERS = {"@radicdavor"}
NATIVE_DEV_TEST_PATH = "scripts/tests/test_native_dev.py"
NATIVE_DEV_NODE_IDS = {
    f"{NATIVE_DEV_TEST_PATH}::test_resolved_identity_encodes_credentials_without_leaking",
    *{
        f"{NATIVE_DEV_TEST_PATH}::test_database_url_preserves_logical_database_identity[{database}]"
        for database in (
            "astra_clinic",
            "demo clinic",
            "demo%clinic",
            "demo/clinic",
            "demo#clinic",
            "demo+clinic",
            "klinika \\u010d",
        )
    },
    f"{NATIVE_DEV_TEST_PATH}::test_database_url_rejects_database_query_delimiter",
    f"{NATIVE_DEV_TEST_PATH}::test_database_url_boundary_failure_does_not_leak_credentials",
    f"{NATIVE_DEV_TEST_PATH}::test_seed_and_serve_preserve_one_logical_database_identity",
    *{
        f"{NATIVE_DEV_TEST_PATH}::test_resolved_identity_rejects_unsafe_config[bad{index}]"
        for index in range(5)
    },
    *{
        f"{NATIVE_DEV_TEST_PATH}::test_database_url_rejects_target_overrides[{host}]"
        for host in ("remote", "db,remote", "127.0.0.1?host=remote")
    },
    f"{NATIVE_DEV_TEST_PATH}::test_seed_keeps_database_url_out_of_command_line",
    f"{NATIVE_DEV_TEST_PATH}::test_seed_build_failure_is_fail_closed",
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
        "image-build-not-required",
        "image_build",
        lambda text: text.replace(
            "The helper requires Compose to build the backend image from the current checkout",
            "The helper may reuse an existing backend image",
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


@dataclass(frozen=True, order=True)
class DependencyInventoryRow:
    ecosystem: str
    directory: str
    surfaces: tuple[str, ...]
    interval: str
    day: str | None


DEPENDABOT_INVENTORY_HEADING = "### Canonical Dependabot inventory"
DEPENDABOT_INVENTORY_HEADER = (
    "ecosystem",
    "directory",
    "tracked surface/manifests",
    "interval",
    "day",
)
README_DEPENDENCY_HEADING = "## Dependencies"
README_DEPENDENCY_CANONICAL_HREF = "docs/dependency-management.md"


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


def _normalize_markdown_cell(value: str) -> str:
    return re.sub(r"`([^`]*)`", r"\1", value).strip()


def _configured_dependency_surfaces(ecosystem: str, directory: str) -> tuple[str, ...]:
    relative_directory = directory.lstrip("/")
    root = ROOT / relative_directory if relative_directory else ROOT
    if ecosystem == "pip":
        candidates = sorted(
            path.relative_to(ROOT).as_posix()
            for pattern in ("requirements*.txt", "*requirements*.txt", "pyproject.toml", "Pipfile", "Pipfile.lock")
            for path in root.glob(pattern)
            if path.is_file()
        )
        assert candidates, f"pip directory {directory!r} has no supported manifest"
        return tuple(dict.fromkeys(candidates))
    if ecosystem == "npm":
        candidates = [root / "package.json", root / "package-lock.json"]
        assert candidates[0].is_file(), f"npm directory {directory!r} has no package.json"
        return tuple(sorted(path.relative_to(ROOT).as_posix() for path in candidates if path.is_file()))
    if ecosystem == "github-actions":
        assert directory == "/"
        assert any((ROOT / ".github" / "workflows").glob("*.yml"))
        return (".github/workflows/*.yml",)
    raise AssertionError(f"unsupported Dependabot ecosystem: {ecosystem!r}")


def _configured_dependabot_inventory(config: dict) -> tuple[DependencyInventoryRow, ...]:
    rows = []
    seen = set()
    for entry in config["updates"]:
        identity = (entry["package-ecosystem"], entry["directory"])
        assert identity not in seen, f"duplicate Dependabot identity: {identity!r}"
        seen.add(identity)
        schedule = entry["schedule"]
        rows.append(
            DependencyInventoryRow(
                ecosystem=identity[0],
                directory=identity[1],
                surfaces=_configured_dependency_surfaces(*identity),
                interval=schedule["interval"].lower(),
                day=schedule.get("day", None).lower() if schedule.get("day") else None,
            )
        )
    return tuple(sorted(rows))


def _documented_dependabot_inventory(markdown: str) -> tuple[DependencyInventoryRow, ...]:
    without_comments = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)
    assert without_comments.count(DEPENDABOT_INVENTORY_HEADING) == 1
    section = without_comments.split(DEPENDABOT_INVENTORY_HEADING, 1)[1]
    section = re.split(r"\n#{1,3} ", section, maxsplit=1)[0]
    table_lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    assert len(table_lines) >= 3, "canonical Dependabot inventory table is missing"
    assert sum(1 for line in section.splitlines() if line.strip().startswith("|")) == len(table_lines)
    cells = [tuple(_normalize_markdown_cell(cell) for cell in line.strip("|").split("|")) for line in table_lines]
    assert tuple(cell.lower() for cell in cells[0]) == DEPENDABOT_INVENTORY_HEADER
    assert all(re.fullmatch(r"-+", cell.replace(":", "")) for cell in cells[1])
    rows = []
    seen = set()
    for raw in cells[2:]:
        assert len(raw) == len(DEPENDABOT_INVENTORY_HEADER)
        assert all(raw), "canonical Dependabot inventory has an empty cell"
        ecosystem, directory, surfaces, interval, day = raw
        identity = (ecosystem.lower(), directory)
        assert identity not in seen, f"duplicate documented Dependabot identity: {identity!r}"
        seen.add(identity)
        rows.append(
            DependencyInventoryRow(
                ecosystem=identity[0],
                directory=identity[1],
                surfaces=tuple(sorted(part.strip() for part in surfaces.split(";") if part.strip())),
                interval=interval.lower(),
                day=None if day.lower() in {"none", "null", "-"} else day.lower(),
            )
        )
    assert rows
    return tuple(sorted(rows))


def _dependency_inventory_dimensions(config: dict, markdown: str) -> dict[str, bool]:
    configured = _configured_dependabot_inventory(config)
    documented = _documented_dependabot_inventory(markdown)
    configured_by_id = {(row.ecosystem, row.directory): row for row in configured}
    documented_by_id = {(row.ecosystem, row.directory): row for row in documented}
    configured_ids = set(configured_by_id)
    documented_ids = set(documented_by_id)
    shared = configured_ids & documented_ids
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()
    )
    surfaces_valid = all(
        configured_by_id[identity].surfaces == documented_by_id[identity].surfaces
        and all(
            surface == ".github/workflows/*.yml"
            or ((ROOT / surface).is_file() and surface in tracked)
            for surface in documented_by_id[identity].surfaces
        )
        for identity in shared
    )
    return {
        "identities": configured_ids == documented_ids,
        "surfaces": surfaces_valid and configured_ids == documented_ids,
        "schedule": configured_ids == documented_ids
        and all(
            (configured_by_id[identity].interval, configured_by_id[identity].day)
            == (documented_by_id[identity].interval, documented_by_id[identity].day)
            for identity in shared
        ),
        "policy": "Dependabot never merges automatically" in markdown
        and "human review" in markdown
        and "pre-approved" in markdown,
    }


def _assert_dependency_inventory_parity(config: dict, markdown: str) -> None:
    dimensions = _dependency_inventory_dimensions(config, markdown)
    failed = sorted(name for name, valid in dimensions.items() if not valid)
    assert not failed, f"Dependabot inventory parity failed: {failed}"


def _markdown_section(markdown: str, heading: str) -> str:
    without_comments = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)
    heading_pattern = rf"(?m)^{re.escape(heading)}\s*$"
    matches = list(re.finditer(heading_pattern, without_comments))
    assert len(matches) == 1, f"expected exactly one {heading!r} section"
    start = matches[0].end()
    level = len(heading.split()[0])
    next_heading = re.search(rf"(?m)^#{{1,{level}}}\s+", without_comments[start:])
    end = start + next_heading.start() if next_heading else len(without_comments)
    return without_comments[start:end]


def _replace_in_readme_dependency_section(
    readme: str, old: str, new: str
) -> str:
    heading_pattern = rf"(?m)^{re.escape(README_DEPENDENCY_HEADING)}\s*$"
    matches = list(re.finditer(heading_pattern, readme))
    assert len(matches) == 1
    start = matches[0].end()
    next_heading = re.search(r"(?m)^#{1,2}\s+", readme[start:])
    end = start + next_heading.start() if next_heading else len(readme)
    section = readme[start:end]
    assert old in section, f"dependency-section mutation fixture not found: {old!r}"
    return readme[:start] + section.replace(old, new, 1) + readme[end:]


def _readme_dependency_dimensions(
    readme: str,
    canonical_markdown: str,
    *,
    tracked: set[str] | None = None,
) -> dict[str, bool]:
    try:
        section = _markdown_section(readme, README_DEPENDENCY_HEADING)
    except AssertionError:
        return {name: False for name in (
            "section", "scripts", "canonical_link", "surfaces", "summary",
            "policy", "schedule", "contradictions",
        )}

    documented = _documented_dependabot_inventory(canonical_markdown)
    canonical_surfaces = {surface for row in documented for surface in row.surfaces}
    if tracked is None:
        tracked = set(
            subprocess.run(
                ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
            ).stdout.splitlines()
        )

    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", section)
    canonical_links = [
        (label, href) for label, href in links if href == README_DEPENDENCY_CANONICAL_HREF
    ]
    canonical_target = ROOT / README_DEPENDENCY_CANONICAL_HREF
    code_paths = {
        value
        for value in re.findall(r"`([^`]+)`", section)
        if "/" in value and not value.startswith(("http://", "https://"))
    }
    required_paths = {
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/package-lock.json",
        "scripts/test-requirements.txt",
    }
    concrete_paths_valid = all(
        path in canonical_surfaces and (ROOT / path).is_file() and path in tracked
        for path in code_paths
    )
    lower = section.lower()
    has_table = any(line.strip().startswith("|") for line in section.splitlines())
    complete_language = "only complete human-readable inventory and schedule" in lower
    policy = (
        "dependabot opens" in lower
        and "neither approves nor merges" in lower
        and "human owner review" in lower
    )
    prohibited_policy = any(
        phrase in lower
        for phrase in (
            "automerge is enabled",
            "automatically approves",
            "owner review is not required",
            "does not require owner review",
        )
    )
    schedule_claimed = bool(re.search(r"\b(daily|weekly|monthly|monday|tuesday|wednesday|thursday|friday)\b", lower))
    return {
        "section": bool(section.strip()),
        "scripts": "CI tooling in `scripts/test-requirements.txt`" in section,
        "canonical_link": len(canonical_links) == 1
        and "dependency" in canonical_links[0][0].lower()
        and canonical_target.is_file()
        and README_DEPENDENCY_CANONICAL_HREF in tracked
        and DEPENDABOT_INVENTORY_HEADING in canonical_markdown,
        "surfaces": required_paths <= code_paths
        and concrete_paths_valid
        and "github actions" in lower,
        "summary": complete_language and not has_table,
        "policy": policy,
        "schedule": not schedule_claimed,
        "contradictions": not prohibited_policy,
    }


def _assert_readme_dependency_consistency(
    readme: str,
    canonical_markdown: str,
    *,
    tracked: set[str] | None = None,
) -> None:
    dimensions = _readme_dependency_dimensions(
        readme, canonical_markdown, tracked=tracked
    )
    failed = sorted(name for name, valid in dimensions.items() if not valid)
    assert not failed, f"README dependency consistency failed: {failed}"


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


def _assert_native_seed_build_contract(source: str) -> None:
    tree = ast.parse(source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    seed_command = functions["seed_command"]
    returns = [node for node in ast.walk(seed_command) if isinstance(node, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.List)
    literals = [
        element.value
        for element in returns[0].value.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    ]
    assert literals == [
        "run", "--build", "--rm", "-e", "DATABASE_URL", "backend", "true"
    ], "native seed must use one active Compose run --build contract"

    seed = functions["seed"]
    run_calls = [
        node
        for node in ast.walk(seed)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
    ]
    assert len(run_calls) == 1
    command = run_calls[0].args[0]
    assert (
        isinstance(command, ast.Call)
        and isinstance(command.func, ast.Name)
        and command.func.id == "seed_command"
    ), "seed must execute the build-bound argv directly"
    assert "sh /app/entrypoint.sh" not in source
    assert "python -m app.seed" not in source
    assert "python -m app.demo.seed" not in source


def _load_native_database_url(source: str) -> Callable:
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "database_url"
    )
    namespace = {"quote": quote, "unquote": unquote, "make_url": make_url}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "native_dev.py", "exec"), namespace)
    return namespace["database_url"]


def _database_url_call(source: str, function_name: str) -> ast.Call:
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "database_url"
    ]
    assert len(calls) == 1, f"{function_name} must use the canonical database_url once"
    return calls[0]


def _native_database_identity_results(source: str) -> dict[str, bool]:
    try:
        build_url = _load_native_database_url(source)
    except (AssertionError, SyntaxError):
        return {name: False for name in (
            "database_identity", "credential_identity", "target_guard", "redaction",
            "seed_identity", "serve_identity", "image_build",
        )}
    values = {
        "POSTGRES_DB": "demo clinic/%+#č",
        "POSTGRES_USER": "synthetic user",
        "POSTGRES_PASSWORD": "synthetic:/@ value%",
    }
    try:
        parsed = make_url(build_url(values, "127.0.0.1", 55432))
        database_identity = parsed.database == values["POSTGRES_DB"]
        credential_identity = (
            parsed.username == values["POSTGRES_USER"]
            and parsed.password == values["POSTGRES_PASSWORD"]
        )
    except Exception:
        database_identity = credential_identity = False
    try:
        build_url({**values, "POSTGRES_DB": "demo?clinic"}, "127.0.0.1", 55432)
        query_delimiter_rejected = False
    except RuntimeError:
        query_delimiter_rejected = True
    database_identity = database_identity and query_delimiter_rejected
    try:
        build_url(values, "remote", 5432)
        target_guard = False
    except RuntimeError:
        target_guard = True
    tree = ast.parse(source)
    database_function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "database_url"
    )
    redaction = all(
        not any(
            isinstance(item, ast.JoinedStr)
            or (isinstance(item, ast.Name) and item.id in {"result", "values", "database", "user", "password"})
            for item in ast.walk(raise_node.exc)
        )
        for raise_node in ast.walk(database_function)
        if isinstance(raise_node, ast.Raise) and raise_node.exc is not None
    )
    try:
        seed_call = _database_url_call(source, "seed")
        seed_identity = (
            len(seed_call.args) == 3
            and isinstance(seed_call.args[0], ast.Name)
            and seed_call.args[0].id == "values"
            and isinstance(seed_call.args[1], ast.Constant)
            and seed_call.args[1].value == "db"
            and isinstance(seed_call.args[2], ast.Constant)
            and seed_call.args[2].value == 5432
        )
    except (AssertionError, StopIteration):
        seed_identity = False
    try:
        serve_call = _database_url_call(source, "serve")
        serve_identity = (
            len(serve_call.args) == 3
            and isinstance(serve_call.args[0], ast.Name)
            and serve_call.args[0].id == "values"
            and isinstance(serve_call.args[1], ast.Constant)
            and serve_call.args[1].value == "127.0.0.1"
            and isinstance(serve_call.args[2], ast.Name)
            and serve_call.args[2].id == "port"
        )
    except (AssertionError, StopIteration):
        serve_identity = False
    try:
        _assert_native_seed_build_contract(source)
        image_build = True
    except AssertionError:
        image_build = False
    return {
        "database_identity": database_identity,
        "credential_identity": credential_identity,
        "target_guard": target_guard,
        "redaction": redaction,
        "seed_identity": seed_identity,
        "serve_identity": serve_identity,
        "image_build": image_build,
    }


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
                "image_build",
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
        "image_build": (
            "The helper requires Compose to build the backend image from the current checkout"
            in native
            and "No prior Full Compose build or manual image\ndeletion is required" in native
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


def test_native_seed_requires_current_backend_build() -> None:
    _assert_native_seed_build_contract(
        (ROOT / "scripts/native_dev.py").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize(
    ("case_id", "mutation"),
    (
        ("missing-build", lambda source: source.replace('        "--build",\n', "")),
        (
            "comment-only-build",
            lambda source: source.replace('        "--build",', '        "--no-deps",  # --build'),
        ),
        (
            "build-after-service",
            lambda source: source.replace(
                '        "--build",\n        "--rm",',
                '        "--rm",\n        "backend",\n        "--build",',
            ).replace('        "backend",\n        "true",', '        "true",', 1),
        ),
        ("wrong-service", lambda source: source.replace('        "backend",', '        "frontend",', 1)),
        ("missing-rm", lambda source: source.replace('        "--rm",\n', "", 1)),
        (
            "shell-entrypoint-workaround",
            lambda source: source.replace('        "true",', '        "sh /app/entrypoint.sh",', 1),
        ),
        (
            "duplicated-base-seed",
            lambda source: source.replace('        "true",', '        "python -m app.seed",', 1),
        ),
        (
            "run-bypasses-build-command",
            lambda source: source.replace("seed_command(args),", "compose_command(args),", 1),
        ),
    ),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_native_seed_build_contract_rejects_mutations(case_id, mutation) -> None:
    source = (ROOT / "scripts/native_dev.py").read_text(encoding="utf-8")
    mutated = mutation(source)
    assert mutated != source, f"{case_id} mutation was ineffective"
    with pytest.raises(AssertionError):
        _assert_native_seed_build_contract(mutated)


NATIVE_DATABASE_MUTATIONS = (
    (
        "remove-database-boundary-validation",
        "database_identity",
        lambda source: source.replace(
            "    if (\n        parsed.database != database",
            "    if (\n        False\n        or parsed.database != parsed.database",
            1,
        ).replace(
            "        or parsed.username != values[\"POSTGRES_USER\"]",
            "        and parsed.username != values[\"POSTGRES_USER\"]",
            1,
        ).replace(
            "        or parsed.password != values[\"POSTGRES_PASSWORD\"]",
            "        and parsed.password != values[\"POSTGRES_PASSWORD\"]",
            1,
        ).replace(
            "        or parsed.host != host", "        and parsed.host != host", 1
        ).replace("        or parsed.port != port", "        and parsed.port != port", 1),
    ),
    (
        "double-encode-database",
        "database_identity",
        lambda source: source.replace(
            '    database = values["POSTGRES_DB"]',
            '    database = quote(quote(values["POSTGRES_DB"], safe=""), safe="")',
            1,
        ),
    ),
    (
        "encoded-database-as-logical-identity",
        "database_identity",
        lambda source: source.replace(
            '    database = values["POSTGRES_DB"]',
            '    database = quote(values["POSTGRES_DB"], safe="")',
            1,
        ),
    ),
    (
        "decode-entire-dsn",
        "credential_identity",
        lambda source: source.replace("    return result", "    return unquote(result)", 1),
    ),
    (
        "space-as-plus",
        "database_identity",
        lambda source: source.replace(
            '    database = values["POSTGRES_DB"]',
            '    database = values["POSTGRES_DB"].replace(" ", "+")',
            1,
        ),
    ),
    (
        "hardcoded-default-database",
        "database_identity",
        lambda source: source.replace(
            '    database = values["POSTGRES_DB"]', '    database = "astra_clinic"', 1
        ),
    ),
    (
        "separate-seed-database",
        "seed_identity",
        lambda source: source.replace(
            'database_url(values, "db", 5432)',
            'database_url({**values, "POSTGRES_DB": "seed_only"}, "db", 5432)',
            1,
        ),
    ),
    (
        "separate-uvicorn-database",
        "serve_identity",
        lambda source: source.replace(
            'database_url(values, "127.0.0.1", port)',
            'database_url({**values, "POSTGRES_DB": "serve_only"}, "127.0.0.1", port)',
            1,
        ),
    ),
    (
        "allow-target-override",
        "target_guard",
        lambda source: source.replace(
            '    if host not in {"127.0.0.1", "db"}:',
            '    if False and host not in {"127.0.0.1", "db"}:',
            1,
        ),
    ),
    (
        "leak-dsn-in-error",
        "redaction",
        lambda source: source.replace(
            'raise RuntimeError("Compose database name cannot be represented safely")',
            'raise RuntimeError(f"Compose database URL cannot be represented: {result}")',
            1,
        ),
    ),
    (
        "remove-run-build",
        "image_build",
        lambda source: source.replace('        "--build",\n', "", 1),
    ),
)


@pytest.mark.parametrize(
    ("case_id", "target", "mutation"),
    NATIVE_DATABASE_MUTATIONS,
    ids=[case[0] for case in NATIVE_DATABASE_MUTATIONS],
)
def test_native_database_identity_rejects_single_fault_mutations(
    case_id: str, target: str, mutation: Callable[[str], str]
) -> None:
    canonical = (ROOT / "scripts/native_dev.py").read_text(encoding="utf-8")
    baseline = _native_database_identity_results(canonical)
    assert all(baseline.values())
    mutated = mutation(canonical)
    assert mutated != canonical, f"{case_id} mutation was ineffective"
    results = _native_database_identity_results(mutated)
    failed = {name for name, passed in results.items() if not passed}
    assert failed == {target}, f"{case_id} was not single-fault: {sorted(failed)}"


def test_native_database_identity_mutation_controls() -> None:
    canonical = (ROOT / "scripts/native_dev.py").read_text(encoding="utf-8")
    mutants = [mutation(canonical) for _, _, mutation in NATIVE_DATABASE_MUTATIONS]
    assert all(mutant != canonical for mutant in mutants)
    assert len(mutants) == len(set(mutants))
    assert _native_database_identity_results(canonical) == {
        "database_identity": True,
        "credential_identity": True,
        "target_guard": True,
        "redaction": True,
        "seed_identity": True,
        "serve_identity": True,
        "image_build": True,
    }
    noop = canonical.replace("obsolete native database builder", "replacement")
    assert noop == canonical
    compound = NATIVE_DATABASE_MUTATIONS[2][2](
        NATIVE_DATABASE_MUTATIONS[-1][2](canonical)
    )
    failed = {
        name
        for name, passed in _native_database_identity_results(compound).items()
        if not passed
    }
    assert failed == {"database_identity", "image_build"}


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


def test_dependabot_documentation_inventory_matches_configuration_bidirectionally() -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    markdown = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    configured = _configured_dependabot_inventory(config)
    documented = _documented_dependabot_inventory(markdown)

    _assert_dependency_inventory_parity(config, markdown)
    assert configured == documented
    assert DependencyInventoryRow(
        "pip",
        "/scripts",
        ("scripts/test-requirements.txt",),
        "weekly",
        "monday",
    ) in configured


def test_dependabot_manifest_discovery_is_nonrecursive_and_git_tracked() -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    rows = _configured_dependabot_inventory(config)
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.splitlines()
    )
    expected = {
        ("npm", "/frontend"): ("frontend/package-lock.json", "frontend/package.json"),
        ("pip", "/backend"): ("backend/requirements.txt",),
        ("pip", "/scripts"): ("scripts/test-requirements.txt",),
        ("github-actions", "/"): (".github/workflows/*.yml",),
    }
    assert {(row.ecosystem, row.directory): row.surfaces for row in rows} == expected
    for row in rows:
        for surface in row.surfaces:
            if surface != ".github/workflows/*.yml":
                assert surface in tracked
                assert (ROOT / surface).is_file()


@pytest.mark.parametrize(
    ("case_id", "old", "new", "failed_dimensions"),
    [
        (
            "missing-scripts-row",
            "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |\n",
            "",
            {"identities", "surfaces", "schedule"},
        ),
        ("wrong-scripts-directory", "| `/scripts` |", "| `/script` |", {"identities", "surfaces", "schedule"}),
        ("wrong-scripts-ecosystem", "| `pip` | `/scripts` |", "| `npm` | `/scripts` |", {"identities", "surfaces", "schedule"}),
        (
            "wrong-scripts-manifest",
            "| `pip` | `/scripts` | `scripts/test-requirements.txt` |",
            "| `pip` | `/scripts` | `scripts/requirements.txt` |",
            {"surfaces"},
        ),
        (
            "nonexistent-manifest",
            "| `pip` | `/scripts` | `scripts/test-requirements.txt` |",
            "| `pip` | `/scripts` | `scripts/missing-requirements.txt` |",
            {"surfaces"},
        ),
        ("wrong-interval", "| Weekly | Monday |", "| Daily | Monday |", {"schedule"}),
        ("wrong-day", "| Weekly | Monday |", "| Weekly | Tuesday |", {"schedule"}),
        (
            "missing-backend-row",
            "| `pip` | `/backend` | `backend/requirements.txt` | Weekly | Monday |\n",
            "",
            {"identities", "surfaces", "schedule"},
        ),
        (
            "missing-npm-row",
            "| `npm` | `/frontend` | `frontend/package.json`; `frontend/package-lock.json` | Weekly | Monday |\n",
            "",
            {"identities", "surfaces", "schedule"},
        ),
        (
            "missing-actions-row",
            "| `github-actions` | `/` | `.github/workflows/*.yml` | Weekly | Monday |\n",
            "",
            {"identities", "surfaces", "schedule"},
        ),
        (
            "extra-documentation-entry",
            "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |",
            "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |\n| `pip` | `/tooling` | `tooling/requirements.txt` | Weekly | Monday |",
            {"identities", "surfaces", "schedule"},
        ),
        ("false-automerge", "Dependabot never merges automatically", "Dependabot merges automatically", {"policy"}),
        ("remove-owner-review", "human review", "automated approval", {"policy"}),
    ],
)
def test_dependabot_documentation_inventory_rejects_single_fault_mutations(
    case_id: str, old: str, new: str, failed_dimensions: set[str]
) -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    assert old in canonical, f"{case_id} fixture no longer matches the canonical document"
    mutated = canonical.replace(old, new, 1)
    assert mutated != canonical, f"{case_id} mutation was ineffective"
    dimensions = _dependency_inventory_dimensions(config, mutated)
    assert {name for name, valid in dimensions.items() if not valid} == failed_dimensions
    with pytest.raises(AssertionError, match="Dependabot inventory parity failed"):
        _assert_dependency_inventory_parity(config, mutated)


@pytest.mark.parametrize(
    ("case_id", "mutation"),
    [
        (
            "duplicate-row",
            lambda text: text.replace(
                "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |",
                "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |\n"
                "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |",
                1,
            ),
        ),
        (
            "duplicate-identity",
            lambda text: text.replace(
                "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |",
                "| `pip` | `/scripts` | `scripts/other.txt` | Weekly | Monday |\n"
                "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |",
                1,
            ),
        ),
        (
            "empty-manifest",
            lambda text: text.replace("| `pip` | `/scripts` | `scripts/test-requirements.txt` |", "| `pip` | `/scripts` |  |", 1),
        ),
        (
            "contradictory-table",
            lambda text: text.replace(
                "This inventory mirrors",
                "| Ecosystem | Directory | Tracked surface/manifests | Interval | Day |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| `pip` | `/scripts` | `scripts/other.txt` | Daily | Tuesday |\n\n"
                "This inventory mirrors",
                1,
            ),
        ),
    ],
)
def test_dependabot_inventory_parser_rejects_ambiguous_tables(case_id, mutation) -> None:
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    mutated = mutation(canonical)
    assert mutated != canonical, f"{case_id} mutation was ineffective"
    with pytest.raises(AssertionError):
        _documented_dependabot_inventory(mutated)


def test_dependabot_inventory_ignores_comment_and_narrative_stuffing() -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    scripts_row = "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |\n"
    without_row = canonical.replace(scripts_row, "", 1)
    for stuffing in (
        "<!-- | pip | /scripts | scripts/test-requirements.txt | Weekly | Monday | -->",
        "The /scripts test-requirements.txt tooling is weekly on Monday.",
    ):
        mutated = without_row.replace(DEPENDABOT_INVENTORY_HEADING, DEPENDABOT_INVENTORY_HEADING + "\n\n" + stuffing, 1)
        with pytest.raises(AssertionError, match="Dependabot inventory parity failed"):
            _assert_dependency_inventory_parity(config, mutated)


def test_dependabot_inventory_noop_and_compound_controls() -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    noop = canonical.replace("not-present-in-canonical", "still-not-present", 1)
    assert noop == canonical
    _assert_dependency_inventory_parity(config, noop)

    compound = canonical.replace(
        "| `pip` | `/scripts` | `scripts/test-requirements.txt` |",
        "| `pip` | `/scripts` | `scripts/missing.txt` |",
        1,
    ).replace(
        "Dependabot never merges automatically", "Dependabot merges automatically", 1
    )
    failed = {name for name, valid in _dependency_inventory_dimensions(config, compound).items() if not valid}
    assert failed == {"surfaces", "policy"}
    assert len(failed) > 1, "compound mutant must not count as a single-fault case"


def test_dependabot_documentation_mutants_have_unique_outputs() -> None:
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    outputs = {
        canonical.replace("/scripts", replacement, 1)
        for replacement in ("/script", "/backend", "/tooling")
    }
    assert canonical not in outputs
    assert len(outputs) == 3


def test_dependabot_yaml_mutations_break_parity_or_validation() -> None:
    canonical_config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    markdown = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")

    removed_scripts = copy.deepcopy(canonical_config)
    removed_scripts["updates"] = [
        entry for entry in removed_scripts["updates"] if entry["directory"] != "/scripts"
    ]
    changed_schedule = copy.deepcopy(canonical_config)
    next(entry for entry in changed_schedule["updates"] if entry["directory"] == "/scripts")["schedule"]["day"] = "tuesday"
    duplicate_identity = copy.deepcopy(canonical_config)
    duplicate_identity["updates"].append(copy.deepcopy(duplicate_identity["updates"][-1]))
    nonexistent_directory = copy.deepcopy(canonical_config)
    next(entry for entry in nonexistent_directory["updates"] if entry["directory"] == "/scripts")["directory"] = "/missing-tooling"
    pip_without_manifest = copy.deepcopy(canonical_config)
    next(entry for entry in pip_without_manifest["updates"] if entry["directory"] == "/scripts")["directory"] = "/backend/tests"

    for mutated in (removed_scripts, changed_schedule):
        with pytest.raises(AssertionError, match="Dependabot inventory parity failed"):
            _assert_dependency_inventory_parity(mutated, markdown)
    for mutated in (duplicate_identity, nonexistent_directory, pip_without_manifest):
        with pytest.raises(AssertionError):
            _assert_dependency_inventory_parity(mutated, markdown)

    with pytest.raises(yaml.constructor.ConstructorError, match="duplicate key"):
        yaml.load("version: 2\nupdates: []\nupdates: []\n", Loader=UniqueKeyLoader)


def test_readme_dependency_summary_matches_canonical_inventory() -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    _assert_dependency_inventory_parity(config, canonical)
    _assert_readme_dependency_consistency(readme, canonical)
    section = _markdown_section(readme, README_DEPENDENCY_HEADING)
    claimed_paths = set(re.findall(r"`([^`]+/[^`]+)`", section))
    assert claimed_paths == {
        "backend/requirements.txt",
        "frontend/package.json",
        "frontend/package-lock.json",
        "scripts/test-requirements.txt",
    }
    assert "|" not in section


@pytest.mark.parametrize(
    ("case_id", "mutation", "failed_dimensions"),
    [
        ("missing-scripts-manifest", lambda text: text.replace(", CI tooling in `scripts/test-requirements.txt`", ""), {"scripts", "surfaces"}),
        ("scripts-directory-typo", lambda text: _replace_in_readme_dependency_section(text, "scripts/test-requirements.txt", "script/test-requirements.txt"), {"scripts", "surfaces"}),
        ("scripts-replaced-by-backend", lambda text: _replace_in_readme_dependency_section(text, "scripts/test-requirements.txt", "backend/requirements.txt"), {"scripts", "surfaces"}),
        ("wrong-scripts-ecosystem", lambda text: text.replace("CI tooling in `scripts/test-requirements.txt`", "frontend npm tooling in `scripts/test-requirements.txt`", 1), {"scripts"}),
        ("missing-canonical-link", lambda text: text.replace("[canonical dependency management inventory](docs/dependency-management.md)", "canonical dependency management inventory", 1), {"canonical_link"}),
        ("nonexistent-canonical-link", lambda text: text.replace("docs/dependency-management.md", "docs/missing-dependency-management.md", 1), {"canonical_link"}),
        ("wrong-canonical-link", lambda text: text.replace("docs/dependency-management.md", "docs/README.md", 1), {"canonical_link"}),
        ("case-mismatched-link", lambda text: text.replace("docs/dependency-management.md", "docs/Dependency-Management.md", 1), {"canonical_link"}),
        ("manifest-outside-section", lambda text: text.replace("CI tooling in `scripts/test-requirements.txt`, and", "CI tooling, and", 1) + "\n\nOutside: `scripts/test-requirements.txt`\n", {"scripts", "surfaces"}),
        ("nonexistent-readme-manifest", lambda text: _replace_in_readme_dependency_section(text, "scripts/test-requirements.txt", "scripts/missing-requirements.txt"), {"scripts", "surfaces"}),
        ("noncanonical-readme-manifest", lambda text: _replace_in_readme_dependency_section(text, "scripts/test-requirements.txt", "scripts/requirements.txt"), {"scripts", "surfaces"}),
        ("stale-readme-schedule", lambda text: text.replace("This is a concise overview", "Updates run weekly. This is a concise overview", 1), {"schedule"}),
        ("false-automerge", lambda text: text.replace("Dependabot opens\nbounded update pull requests, but it neither approves nor merges them", "Dependabot opens bounded update pull requests; automerge is enabled", 1), {"policy", "contradictions"}),
        ("remove-owner-review", lambda text: text.replace("Every\nproposal requires human owner review", "Owner review is not required", 1), {"policy", "contradictions"}),
        ("competing-full-table", lambda text: text.replace("Known advisories", "| Ecosystem | Directory |\n| --- | --- |\n| pip | /backend |\n\nKnown advisories", 1), {"summary"}),
        ("duplicate-dependency-section", lambda text: text.replace("## Contributing", "## Dependencies\n\nContradictory inventory.\n\n## Contributing", 1), {"section", "scripts", "canonical_link", "surfaces", "summary", "policy", "schedule", "contradictions"}),
    ],
)
def test_readme_dependency_summary_rejects_single_fault_mutations(
    case_id: str, mutation: Callable[[str], str], failed_dimensions: set[str]
) -> None:
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    mutated = mutation(readme)
    assert mutated != readme, f"{case_id} mutation was ineffective"
    dimensions = _readme_dependency_dimensions(mutated, canonical)
    assert {name for name, valid in dimensions.items() if not valid} == failed_dimensions
    with pytest.raises(AssertionError, match="README dependency consistency failed"):
        _assert_readme_dependency_consistency(mutated, canonical)


def test_readme_dependency_summary_rejects_comment_stuffing() -> None:
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = _markdown_section(readme, README_DEPENDENCY_HEADING)
    without_scripts = readme.replace("CI tooling in `scripts/test-requirements.txt`, and", "CI tooling, and", 1)
    comment_stuffed = without_scripts.replace(
        README_DEPENDENCY_HEADING,
        README_DEPENDENCY_HEADING + "\n\n<!-- CI tooling in `scripts/test-requirements.txt` -->",
        1,
    )
    link_stuffed = readme.replace(
        "[canonical dependency management inventory](docs/dependency-management.md)",
        "<!-- [canonical dependency management inventory](docs/dependency-management.md) -->",
        1,
    )
    assert "scripts/test-requirements.txt" in section
    for mutated in (comment_stuffed, link_stuffed):
        with pytest.raises(AssertionError, match="README dependency consistency failed"):
            _assert_readme_dependency_consistency(mutated, canonical)


def test_readme_dependency_summary_noop_compound_and_uniqueness_controls() -> None:
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    noop = readme.replace("not-present-in-readme", "still-not-present", 1)
    assert noop == readme
    _assert_readme_dependency_consistency(noop, canonical)

    compound = _replace_in_readme_dependency_section(
        readme, "scripts/test-requirements.txt", "scripts/missing.txt"
    ).replace(
        "Every\nproposal requires human owner review", "Owner review is not required", 1
    )
    failed = {name for name, valid in _readme_dependency_dimensions(compound, canonical).items() if not valid}
    assert failed == {"scripts", "surfaces", "policy", "contradictions"}
    assert len(failed) > 1

    outputs = {
        _replace_in_readme_dependency_section(
            readme, "scripts/test-requirements.txt", replacement
        )
        for replacement in (
            "script/test-requirements.txt",
            "scripts/missing-requirements.txt",
            "backend/requirements.txt",
        )
    }
    assert readme not in outputs
    assert len(outputs) == 3


def test_readme_dependency_summary_rejects_untracked_manifest() -> None:
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    tracked = set(
        subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    )
    tracked.remove("scripts/test-requirements.txt")
    dimensions = _readme_dependency_dimensions(readme, canonical, tracked=tracked)
    assert {name for name, valid in dimensions.items() if not valid} == {"surfaces"}


def test_readme_dependency_summary_rejects_canonical_drift() -> None:
    config = _load_yaml(ROOT / ".github" / "dependabot.yml")
    canonical = (ROOT / "docs" / "dependency-management.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    yaml_new_surface = copy.deepcopy(config)
    yaml_new_surface["updates"].append(
        {"package-ecosystem": "pip", "directory": "/", "schedule": {"interval": "weekly", "day": "monday"}}
    )
    with pytest.raises(AssertionError):
        _assert_dependency_inventory_parity(yaml_new_surface, canonical)

    canonical_changed_manifest = canonical.replace(
        "scripts/test-requirements.txt", "scripts/requirements.txt"
    )
    with pytest.raises(AssertionError):
        _assert_readme_dependency_consistency(readme, canonical_changed_manifest)

    canonical_without_scripts = canonical.replace(
        "| `pip` | `/scripts` | `scripts/test-requirements.txt` | Weekly | Monday |\n", "", 1
    )
    with pytest.raises(AssertionError):
        _assert_readme_dependency_consistency(readme, canonical_without_scripts)

    contradictory_readme = readme.replace(
        "This is a concise overview", "This complete inventory runs daily"
    )
    with pytest.raises(AssertionError):
        _assert_readme_dependency_consistency(contradictory_readme, canonical)
