from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FULL_CORE_SHARD_COUNT = 2

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


def full_core_test_shards() -> tuple[tuple[str, ...], ...]:
    files = tuple(
        path.relative_to(BACKEND).as_posix()
        for path in sorted((BACKEND / "tests").glob("test_*.py"))
    )
    midpoint = (len(files) + 1) // FULL_CORE_SHARD_COUNT
    return (files[:midpoint], files[midpoint:])


def _run_pytest_subprocess(arguments: list[str]) -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *arguments],
        cwd=BACKEND,
        check=False,
    )
    return int(completed.returncode)


def run_full_gate(
    extra_arguments: list[str],
    *,
    runner=_run_pytest_subprocess,
) -> int:
    common = ["-m", "not integration", "-ra", "--durations=50", *extra_arguments]
    shards = full_core_test_shards()
    with ThreadPoolExecutor(max_workers=FULL_CORE_SHARD_COUNT) as executor:
        results = tuple(
            executor.map(
                runner,
                ([*shard, *common] for shard in shards),
            )
        )
    if any(results):
        return next(result for result in results if result)
    return runner(["tests/integration", "-q", "-rs", *extra_arguments])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a documented ASTRA test layer")
    parser.add_argument("gate", choices=("fast", "integration", "full"))
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    if args.gate == "full":
        return run_full_gate(args.pytest_args)
    return int(pytest.main([*gate_arguments(args.gate), *args.pytest_args]))


if __name__ == "__main__":
    raise SystemExit(main())
