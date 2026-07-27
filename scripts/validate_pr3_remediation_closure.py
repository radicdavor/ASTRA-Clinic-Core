from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "security" / "pr3-remediation-behavioural-review-units.json"
REQUIRED_REVIEW_UNITS = {
    "populated_legacy_upgrade",
    "transitional_workflow_rediscovery",
    "cross_scope_dto_projection",
    "context_initialization",
    "deployment_proxy_boundary",
}
REQUIRED_COVERAGE_DIMENSIONS = {
    "source_file_coverage",
    "security_boundary_coverage",
    "workflow_transition_coverage",
    "legacy_upgrade_coverage",
    "negative_authorization_coverage",
    "deployment_topology_coverage",
}


def validate() -> dict[str, int]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    units = {unit["id"]: unit for unit in payload.get("review_units", [])}
    missing_units = REQUIRED_REVIEW_UNITS - units.keys()
    if missing_units:
        raise RuntimeError(f"Missing behavioural review units: {sorted(missing_units)}")

    evidence_count = 0
    for unit_id in sorted(REQUIRED_REVIEW_UNITS):
        evidence = units[unit_id].get("evidence") or []
        if not evidence:
            raise RuntimeError(f"Review unit {unit_id} has no executable evidence")
        for item in evidence:
            path = ROOT / item["path"]
            if not path.is_file():
                raise RuntimeError(f"Review evidence file is missing: {item['path']}")
            source = path.read_text(encoding="utf-8")
            if item["selector"] not in source:
                raise RuntimeError(
                    f"Review evidence selector is missing: {item['path']}::{item['selector']}"
                )
            evidence_count += 1

    dimensions = payload.get("coverage_dimensions") or {}
    missing_dimensions = REQUIRED_COVERAGE_DIMENSIONS - dimensions.keys()
    if missing_dimensions:
        raise RuntimeError(f"Missing coverage dimensions: {sorted(missing_dimensions)}")
    for name in REQUIRED_COVERAGE_DIMENSIONS:
        referenced_units = dimensions[name]
        if not referenced_units:
            raise RuntimeError(f"Coverage dimension {name} has no review units")
        unknown = set(referenced_units) - units.keys()
        if unknown:
            raise RuntimeError(f"Coverage dimension {name} references unknown units: {sorted(unknown)}")

    return {
        "review_units": len(REQUIRED_REVIEW_UNITS),
        "evidence_selectors": evidence_count,
        "coverage_dimensions": len(REQUIRED_COVERAGE_DIMENSIONS),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
