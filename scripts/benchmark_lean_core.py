from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import statistics
import sys
from time import perf_counter
from typing import Iterator

from sqlalchemy import event


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@dataclass
class SqlSample:
    durations_ms: list[float] = field(default_factory=list)
    categories: Counter[str] = field(default_factory=Counter)
    category_durations_ms: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def total_ms(self) -> float:
        return sum(self.durations_ms)


def statement_category(statement: str) -> str:
    normalized = " ".join(statement.lower().split())
    if "audit_logs" in normalized:
        return "audit"
    if any(name in normalized for name in ("user_sessions", "clinic_memberships", "users", "roles", "permissions")):
        return "authorization"
    return "domain"


@contextmanager
def track_sql() -> Iterator[SqlSample]:
    sample = SqlSample()

    def before(_conn, _cursor, _statement, _parameters, context, _executemany):
        context._astra_started_at = perf_counter()

    def after(_conn, _cursor, statement, _parameters, context, _executemany):
        duration_ms = (perf_counter() - context._astra_started_at) * 1000
        category = statement_category(statement)
        sample.durations_ms.append(duration_ms)
        sample.categories[category] += 1
        sample.category_durations_ms[category] += duration_ms

    event.listen(engine, "before_cursor_execute", before)
    event.listen(engine, "after_cursor_execute", after)
    try:
        yield sample
    finally:
        event.remove(engine, "before_cursor_execute", before)
        event.remove(engine, "after_cursor_execute", after)


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    rank = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[rank]


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "min": round(min(values), 2),
        "p50": round(statistics.median(values), 2),
        "p95": round(percentile(values, 0.95), 2),
        "max": round(max(values), 2),
        "standard_deviation": round(statistics.pstdev(values), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile ASTRA lean-core read projections on synthetic data")
    parser.add_argument("--seed-file", type=Path, required=True)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if "DATABASE_URL" not in os.environ:
        parser.error("DATABASE_URL must point to an isolated synthetic PostgreSQL database")
    if args.warmups < 3 or args.samples < 20:
        parser.error("Use at least 3 warmups and 20 measured samples")

    seed = json.loads(args.seed_file.read_text(encoding="utf-8"))
    endpoints = {
        "daily_dashboard": (f"/api/dashboard/day?selected_date={seed['date']}", "adminA"),
        "patient_directory": ("/api/patients?q=E2E", "adminA"),
        "clinical_record": (f"/api/patients/{seed['patients']['shared']}/clinical-record", "physicianA"),
        "signed_report": (f"/api/signed-reports/{seed['clinical']['signedReport']}", "physicianA"),
    }

    results: dict[str, object] = {
        "environment": {
            "database": engine.url.render_as_string(hide_password=True),
            "warmups": args.warmups,
            "samples": args.samples,
            "transport": "FastAPI TestClient; PostgreSQL; browser session; clinic scope",
        },
        "endpoints": {},
    }
    with TestClient(app) as client:
        headers = {"X-Clinic-Id": str(seed["clinics"]["a"])}
        for name, (path, user_key) in endpoints.items():
            client.cookies.clear()
            login = client.post(
                "/auth/browser/login",
                json={"email": seed["users"][user_key], "password": seed["password"]},
            )
            login.raise_for_status()
            for _ in range(args.warmups):
                response = client.get(path, headers=headers)
                response.raise_for_status()

            elapsed: list[float] = []
            sql_elapsed: list[float] = []
            app_elapsed: list[float] = []
            query_counts: list[int] = []
            response_sizes: list[int] = []
            categories: Counter[str] = Counter()
            category_elapsed: dict[str, list[float]] = defaultdict(list)
            for _ in range(args.samples):
                with track_sql() as sql:
                    started = perf_counter()
                    response = client.get(path, headers=headers)
                    total_ms = (perf_counter() - started) * 1000
                response.raise_for_status()
                elapsed.append(total_ms)
                sql_elapsed.append(sql.total_ms)
                app_elapsed.append(max(0.0, total_ms - sql.total_ms))
                query_counts.append(len(sql.durations_ms))
                response_sizes.append(len(response.content))
                categories.update(sql.categories)
                for category in ("authorization", "audit", "domain"):
                    category_elapsed[category].append(sql.category_durations_ms.get(category, 0.0))

            results["endpoints"][name] = {
                "path": path,
                "actor": user_key,
                "latency_ms": summarize(elapsed),
                "sql_ms": summarize(sql_elapsed),
                "application_and_serialization_ms": summarize(app_elapsed),
                "query_count": {
                    "min": min(query_counts),
                    "max": max(query_counts),
                    "median": statistics.median(query_counts),
                },
                "query_categories_total": dict(sorted(categories.items())),
                "query_category_ms": {
                    category: summarize(values)
                    for category, values in sorted(category_elapsed.items())
                },
                "response_bytes": {
                    "min": min(response_sizes),
                    "max": max(response_sizes),
                },
            }

    rendered = json.dumps(results, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
