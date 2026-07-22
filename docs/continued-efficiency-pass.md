# Lean Core Optimization — Continued Efficiency Pass

Measured: 22 July 2026

Scope: local synthetic data only; branch
`feature/full-stack-production-validation`; no production deployment, real
patient data, external provider, cache, queue or new runtime service.

## Reproducible setup

- Windows 11, Intel Core i7-4700HQ (4 cores / 8 logical processors)
- PostgreSQL 16.14 in the existing local Docker container
- Python 3.12 validation virtual environment; Node 24.18.0
- one Uvicorn worker
- fresh database `astra_efficiency_20260722`, migrated from empty to 0062
- `scripts/seed_full_stack_e2e.py` synthetic fixture
- 20,004 synthetic patients for directory/query-plan measurements
- browser-session authentication, active-clinic header and real role policies
- 3 warm-up requests and 30 measured requests per core endpoint
- FastAPI `TestClient` transport to isolate application/DB behavior from local
  browser and Docker-network noise

Run the endpoint profiler with an isolated database and seed file:

```powershell
$env:DATABASE_URL='postgresql+psycopg://.../isolated_database'
$env:JWT_SECRET='local-synthetic-secret'
backend\.localrun-venv\Scripts\python.exe scripts\benchmark_lean_core.py `
  --seed-file .localrun\efficiency-seed.json --warmups 3 --samples 30
```

## Four endpoint decisions

| Endpoint | Late Module 3.5 p50 / p95 | Controlled p50 / p95 | SQL queries | Response | Dominant cost | Decision |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Daily dashboard | 272.92 / 1,083.69 ms | 68.00 / 89.60 ms | 11 stable | 3,082 B | 6 auth/context + 5 domain statements | ACCEPTABLE AS-IS |
| Patient search (`q=E2E`, 20k patients) | 180.19 / 363.93 ms | 106.41 / 186.98 ms | 7 stable | 1,060 B | leading-wildcard sequential scan, 72.06 ms plan | ACCEPTABLE AS-IS |
| Institution clinical record | 326.77 / 616.18 ms | 46.90 / 63.10 ms | 11 stable | 853 B | scoped policy plus one reliable read-audit insert | ACCEPTABLE AS-IS |
| Signed report | 335.41 / 693.85 ms | 42.10 / 55.11 ms | 10 stable | 568 B | scope/integrity verification plus one read-audit insert | ACCEPTABLE AS-IS |

The earlier late-run failures are not reproducible under a controlled dataset
and host state. No endpoint cache, materialized view, denormalization or new
service is justified.

## Verified high-value fix: bounded directory

The unfiltered patient directory was the one reproducible defect found during
the continuation. At 20,004 synthetic patients it returned every row:

| Unfiltered directory | Before | After |
| --- | ---: | ---: |
| rows | 20,004 | 50 |
| response bytes | 5,327,758 | 12,928 |
| p50 | 1,552.73 ms | 38.50 ms |
| p95 | 2,032.89 ms | 45.83 ms |
| maximum | 2,107.82 ms | 45.99 ms |

The p95 reduction is 97.7%. The endpoint now has a validated maximum of 50 and
stable `(last_name, first_name, id)` ordering. Other potentially large list
surfaces now retain their existing list response contract but have explicit
maximums: appointments 200, clinical documents 100, document addenda 100,
patient appointment history 200, patient invoices 100 and delivery history
100. Audit remains capped at 200 with an ID tie-breaker.

## Query plans, authorization and audit

- Bounded directory uses `ix_patients_last_name` plus incremental sort and
  finishes in 0.40 ms with no temporary writes.
- Wildcard patient search scans 20,004 rows and finishes in 72.06 ms. Because
  the authenticated API remains below its 300 ms p95 budget, `pg_trgm` is
  deferred; its extension/write cost is not justified yet.
- Clinical metadata uses `ix_clinical_documents_patient_id` and finishes in
  0.19 ms.
- Dashboard core selection uses journey clinic, appointment date and activity
  clinic indexes and finishes in 0.43 ms.
- Signed report lookup uses its primary key and finishes in 0.09 ms.
- Auth/current-clinic context consistently contributes six statements per
  scoped request. Dependencies reuse one request-scoped context; no global or
  cross-request authorization cache exists, so revocation still applies on the
  next request.
- Clinical record and signed report each perform exactly one audit insert in
  the request transaction. Audit is not moved to a lossy background task.

## Frontend and runtime review

The request and memory review in `lean-core-frontend-analysis.md` remains
current. There is no interval polling, no Blob URL creation and no retained
source-file cache. Superseded reads use `AbortController`; listeners in modals,
forms, toast host and reception are removed on cleanup. Full clinical content
loads only after route/detail selection.

The current SQLAlchemy engine uses the standard bounded QueuePool rather than
an application-specific oversized pool. No pool tuning is committed without a
deployment concurrency measurement. One Uvicorn worker remains the small
deployment recommendation; adding workers multiplies both memory and DB pools.

### Idle and worker measurements

A clean 21-sample idle run covered 628.2 seconds, with one sample every 30
seconds. No tests or benchmark traffic ran during the interval:

- backend CPU increased by 0.0469 seconds;
- backend RSS stayed between 181.52 and 181.62 MiB and ended 0.02 MiB lower;
- the database held exactly two application connections throughout;
- the backend access log gained zero lines.

The PostgreSQL CPU samples include the `docker stats` and `pg_stat_activity`
measurement probes themselves; those probes explain the brief reported CPU
spikes. The stable backend RSS, connection count and access log provide no
evidence of an idle memory leak, unbounded pool growth or background polling.

A separate modest-concurrency check sent 40 `/ready` requests at concurrency
10. It includes the PostgreSQL readiness query and was run once per worker
configuration:

| Uvicorn workers | Startup | p50 / p95 | Total process RSS | DB connections including measurement probe |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 6.25 s | 73.62 / 168.72 ms | 200.88 MiB | 6 |
| 2 | 7.90 s | 43.02 / 1,060.44 ms | 426.22 MiB | 10 |

Two workers more than doubled memory and connection use and produced a worse
p95 on this host. The evidence therefore supports retaining one worker and the
default bounded SQLAlchemy pool. Production concurrency must be remeasured on
the deployment host before changing either setting.

## Alembic preflight

There is one migration head and empty upgrade succeeds. `alembic check` reports
80 historical metadata comparison operations, all classified in
`docs/alembic-metadata-drift.md`. No autogenerated migration or broad ignore is
used. The migrated schema is canonical; no verified backup/restore blocker was
found.

Empty upgrade to 0062, downgrade to 0060 and re-upgrade to 0062 all passed on
an isolated PostgreSQL database. Development and production-example Compose
configurations also parse with explicit validation-only production values.

## Validation

| Gate | Result |
| --- | --- |
| focused PostgreSQL dashboard/patient/record/report tests | 38 passed |
| backend fast suite | 145 passed |
| PostgreSQL integration suite | 16 passed |
| backend full suite | 688 passed, 1 expected Windows POSIX skip |
| frontend dependency audit | `npm ci`, 0 vulnerabilities |
| frontend typecheck | passed |
| frontend contract tests | 4 passed |
| frontend Vitest | 57 passed |
| frontend smoke | passed |
| frontend production build | passed |
| route-mocked Playwright | 1 passed |
| DB-backed Playwright | 10 tests, exit 0 with its own backend on port 8011 |
| OpenAPI generated-type drift | passed |
| Alembic empty upgrade / downgrade / re-upgrade | passed |
| development and production-example Compose parsing | passed |

The full backend run took 1,054.68 seconds. The DB-backed browser orchestration
took 98.1 seconds in the retained rerun. `alembic check` remains intentionally
non-zero because of the exhaustively classified historical metadata drift; it
is not represented as a passing gate.

## Rejected optimizations

- `pg_trgm` for wildcard patient search: current p95 passes and the dataset is
  within the stated near-term capacity.
- dashboard/record/report caching: results are already within budget and a
  cache would complicate authorization revocation and clinical freshness.
- materialized views or denormalization: no query plan requires them.
- asynchronous read audit: would weaken reliable audit for a negligible gain.
- extra Uvicorn workers by default: increases memory and connection capacity
  before throughput evidence exists.
- broad Alembic comparison ignores or autogenerated schema cleanup: would hide
  or destructively rewrite intentional migration-owned objects.

## Decision

`LEAN CORE OPTIMIZATION SATURATED — READY FOR MODULE 4`

Module 4 is not started by this work.
