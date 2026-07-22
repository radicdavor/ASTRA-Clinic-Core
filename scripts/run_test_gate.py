from __future__ import annotations

import argparse
from pathlib import Path
import os
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

FAST_TESTS = (
    "tests/test_contract_hardening.py",
    "tests/test_dashboard_operational_status.py",
    "tests/test_clinic_time.py",
    "tests/test_clinical_evidence_timeline_contract.py",
    "tests/test_clinical_finding_extraction_contract.py",
    "tests/test_clinical_open_questions_contract.py",
    "tests/test_clinical_review_contract.py",
    "tests/test_schema_readiness.py",
    "tests/test_module_manifest_loader.py",
    "tests/test_gastroenterology_protocol_seeds.py",
    "tests/test_gastroscopy_protocol_migration.py",
    "tests/test_cli.py",
    "tests/test_test_gate.py",
)


def gate_arguments(gate: str) -> list[str]:
    if gate == "fast":
        return [*FAST_TESTS, "-q"]
    if gate == "integration":
        return ["tests/integration", "-q", "-rs"]
    return ["-ra", "--durations=50"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a documented ASTRA test layer")
    parser.add_argument("gate", choices=("fast", "integration", "full"))
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    return int(pytest.main([*gate_arguments(args.gate), *args.pytest_args]))


if __name__ == "__main__":
    raise SystemExit(main())
