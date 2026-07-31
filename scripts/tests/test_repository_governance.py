from __future__ import annotations

import re
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
    assert "currently has no `LICENSE`" in text
    assert "production" in text and "real patient data" in text


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
