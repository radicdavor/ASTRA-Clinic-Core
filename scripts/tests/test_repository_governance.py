from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
ALLOWED_CODEOWNERS = {"@radicdavor"}


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
    seed_command = (
        "docker compose run --rm "
        "-e DATABASE_URL=postgresql+psycopg://astra:astra@db:5432/astra_clinic "
        "backend true"
    )
    assert seed_command in native_commands
    assert not any(
        "alembic upgrade head" in block and "cd backend" in block
        for _, block in native_blocks
    ), "migration guidance must not mix host cwd and container DNS"

    uvicorn_blocks = [
        (language, block)
        for language, block in native_blocks
        if any("uvicorn" in line for line in block)
    ]
    assert {language for language, _ in uvicorn_blocks} == {"bash", "powershell"}
    assert len(uvicorn_blocks) == 2, "README must define bash and PowerShell host blocks"
    for language, block in uvicorn_blocks:
        joined = "\n".join(block)
        assert "127.0.0.1:5432/astra_clinic" in joined
        assert not any(
            "@db:5432" in line and line != seed_command for line in block
        ), "only the one-shot seed container may use Compose-only DB DNS"
        assert "cd backend" not in block
        assert "--app-dir backend" in joined
        assert "--port 8000" in joined
        assert "DOCUMENT_STORAGE_PATH" in joined
        assert "/app/data/documents" not in joined
        assert ".astra-dev" in joined and "documents" in joined
        assert "APP_ENV" in joined and "development" in joined
        assert "DEMO_MODE" in joined and "true" in joined
        assert "REAL_DATA_ALLOWED" in joined and "false" in joined
        assert block.index(seed_command) < next(
            index for index, line in enumerate(block) if "uvicorn" in line
        )
        if language == "bash":
            assert "mkdir -p" in joined and "$(pwd)" in joined
            assert "$env:" not in joined and "New-Item" not in joined
        else:
            assert "Join-Path (Get-Location)" in joined and "New-Item" in joined
            assert "export " not in joined and "$(pwd)" not in joined
    assert "`docker compose down`" in native
    assert ".astra-dev/" in gitignore.splitlines()
    assert "they do not prove\nthat demo users exist" in native
    assert "successful synthetic login is not evidence of production readiness" in native
    assert "never run the demo seed against a production database" in native.lower()
    _assert_entrypoint_sequence(entrypoint)


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


@pytest.mark.parametrize(
    ("mutation", "gitignore_mutation"),
    (
        (
            lambda text: text.replace(
                "### Option B: native backend with Compose PostgreSQL",
                "### Option B: native backend with Compose PostgreSQL\n\n```bash\ndocker compose up --build\n```",
            ),
            lambda text: text,
        ),
        (
            lambda text: text.replace("docker compose up -d db", "docker compose up -d"),
            lambda text: text,
        ),
        (
            lambda text: text.replace("docker compose up -d db", "docker compose up -d backend"),
            lambda text: text,
        ),
        (
            lambda text: text.replace("export DOCUMENT_STORAGE_PATH=\"$(pwd)/.astra-dev/documents\"", "")
            .replace("$env:DOCUMENT_STORAGE_PATH = $storage", ""),
            lambda text: text,
        ),
        (
            lambda text: text.replace(".astra-dev/documents", "/app/data/documents")
            .replace(".astra-dev\\documents", "/app/data/documents"),
            lambda text: text,
        ),
        (
            lambda text: text.replace("@127.0.0.1:5432/astra_clinic", "@db:5432/astra_clinic"),
            lambda text: text,
        ),
        (lambda text: text, lambda text: text.replace(".astra-dev/", "")),
        (
            lambda text: text.replace("mkdir -p \"$(pwd)/.astra-dev/documents\"", "$storage = Join-Path (Get-Location) '.astra-dev'", 1),
            lambda text: text,
        ),
        (
            lambda text: text.replace("--port 8000", "--port 8001"),
            lambda text: text,
        ),
        (
            lambda text: text.replace(
                "docker compose run --rm -e DATABASE_URL=postgresql+psycopg://astra:astra@db:5432/astra_clinic backend true",
                "",
            ),
            lambda text: text,
        ),
        (
            lambda text: text.replace(
                "docker compose run --rm -e DATABASE_URL=postgresql+psycopg://astra:astra@db:5432/astra_clinic backend true\npython -m uvicorn",
                "python -m uvicorn",
            ).replace(
                "--app-dir backend --port 8000",
                "--app-dir backend --port 8000\ndocker compose run --rm -e DATABASE_URL=postgresql+psycopg://astra:astra@db:5432/astra_clinic backend true",
            ),
            lambda text: text,
        ),
        (
            lambda text: text.replace(
                "backend true", "--entrypoint python backend -m app.demo.seed"
            ),
            lambda text: text,
        ),
        (
            lambda text: text.replace("backend true", "backend sh /app/entrypoint.sh true"),
            lambda text: text,
        ),
        (
            lambda text: text.replace(
                "they do not prove\nthat demo users exist",
                "they prove that demo users exist",
            ),
            lambda text: text,
        ),
        (
            lambda text: text.replace("APP_ENV=development", "APP_ENV=production")
            .replace('$env:APP_ENV = "development"', '$env:APP_ENV = "production"'),
            lambda text: text,
        ),
    ),
)
def test_readme_database_guidance_rejects_context_mutations(
    mutation, gitignore_mutation
) -> None:
    with pytest.raises(AssertionError):
        _assert_database_guidance(
            mutation((ROOT / "README.md").read_text(encoding="utf-8")),
            _load_yaml(ROOT / "docker-compose.yml"),
            gitignore_mutation((ROOT / ".gitignore").read_text(encoding="utf-8")),
            (ROOT / "backend/entrypoint.sh").read_text(encoding="utf-8"),
        )


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
    assert actual == {("npm", "/frontend"), ("pip", "/backend"), ("github-actions", "/")}
    assert (ROOT / "frontend").is_dir() and (ROOT / "backend").is_dir()
    assert all(entry["open-pull-requests-limit"] <= 5 for entry in updates)
    assert all(entry["schedule"]["interval"] == "weekly" for entry in updates)
    assert "automerge" not in raw.lower()
