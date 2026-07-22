# ASTRA Clinic Core performance budget

Status: Module 3.5 Increment A baseline

Measured: 22 July 2026

Scope: synthetic/demo data only

## Purpose

This budget defines the smallest useful performance contract for the current
React, FastAPI and PostgreSQL architecture. It is a regression guard, not a
promise of internet latency or production capacity. Clinical and security
invariants take precedence over every performance target.

The intended near-term capacity is:

- 1–5 concurrent users in one clinic;
- 20–50 concurrent users across one institution;
- hundreds of appointments per day;
- tens of thousands of patients;
- hundreds of thousands of clinical documents.

These assumptions do not justify caches, queues, extra services or distributed
infrastructure without new measurements.

## API latency budgets

Measure warm requests against PostgreSQL from the same host. Use at least 20
requests and report p50, p95 and maximum. Authentication and authorization must
remain enabled.

| Operation | p95 budget |
| --- | ---: |
| `GET /health` | 50 ms |
| `GET /ready` | 250 ms |
| daily clinic dashboard | 500 ms |
| patient directory/search | 300 ms |
| patient clinical record page | 500 ms |
| signed report read | 300 ms |
| appointment creation | 500 ms |

Appointment creation is a write-path budget and must be measured with a unique,
valid synthetic appointment. Repeated write benchmarks must clean up their own
isolated data and must not weaken conflict, audit or authorization checks.

## SQL query budgets

Query counts exclude authentication/session setup unless a test explicitly
states otherwise. A query-count regression is actionable even when local
latency remains below budget.

| Operation | Query budget |
| --- | ---: |
| daily clinic dashboard | 5–8 |
| patient clinical record page | 3–6 |
| signed report read | 2–4 |
| patient directory | one result query plus one count query when pagination requires a count |

The directory endpoint may omit a count query while it returns a deliberately
bounded suggestion list rather than a paginated result set.

## Frontend and runtime budgets

| Measurement | Budget |
| --- | ---: |
| production frontend preview startup | 3 s |
| backend readiness after process start | 20 s |
| frontend production-preview idle CPU | below 2% after stabilization |
| backend idle CPU | below 2% after stabilization |
| initial application JavaScript, uncompressed | 500 KiB |
| any route-specific JavaScript chunk, uncompressed | 150 KiB |
| initial application CSS, uncompressed | 150 KiB |

Route splitting is only considered effective when a route-specific chunk is not
eagerly fetched on an unrelated initial route. File names alone are not proof of
lazy loading.

## Increment A measured baseline

### Test and build duration

The backend used a newly created PostgreSQL database migrated from zero to
Alembic head. The frontend used a fresh `npm ci` and the checked-in lockfile.

| Check | Result | Wall time |
| --- | --- | ---: |
| backend full suite | 681 passed | 710.93 s |
| frontend `npm ci` | passed | 77.08 s |
| frontend typecheck | passed | 32.52 s |
| frontend unit/contract tests | 54 unit + 4 contract passed | 28.08 s |
| frontend smoke test | passed | 2.76 s |
| frontend build | passed | 35.17 s |
| OpenAPI contract generation/check | passed | 13.67 s |
| route-mocked Playwright | 1 passed | 37.98 s |
| PostgreSQL-backed Playwright | 10 passed | 109.01 s |

The five slowest backend test calls were 5.19 s, 4.40 s, 3.98 s, 3.66 s and
3.39 s. Repeated PostgreSQL fixture setup contributed roughly 2.2–3.4 s to many
integration tests, so test-environment setup is a measured optimization target;
it is not evidence that the corresponding API is slow.

### Warm API latency

The sample used an isolated migrated database, the full-stack E2E synthetic
seed, revocable browser sessions, clinic context headers and 20 sequential warm
requests per endpoint.

| Operation | median | p95 | max | Budget result |
| --- | ---: | ---: | ---: | --- |
| health | 5.85 ms | 6.76 ms | 7.10 ms | pass |
| readiness | 359.96 ms | 524.98 ms | 815.12 ms | **fail** |
| daily dashboard | 77.70 ms | 120.30 ms | 601.05 ms | pass at p95 |
| patient directory | 41.92 ms | 58.77 ms | 70.17 ms | pass |
| patient clinical record | 69.83 ms | 194.28 ms | 212.25 ms | pass |
| signed report | 60.46 ms | 172.08 ms | 255.11 ms | pass |

The readiness endpoint is the only measured p95 budget failure in this sample.
The dashboard maximum is recorded but does not breach the p95 contract.

### Startup, memory and idle behavior

| Measurement | Baseline |
| --- | ---: |
| backend process to successful readiness | 12.37 s |
| built frontend preview to successful HTTP response | 1.38 s |
| Uvicorn worker working set | 209.2 MiB |
| frontend preview working set | 66.6 MiB |
| shared PostgreSQL container working set | 172–179 MiB |
| stabilized existing backend CPU over 10 s | 0 ms |
| frontend preview CPU over 5 s | 62.5 ms |

An early five-second CPU sample from the newly started backend captured 3.02 s
of processor time while startup work was still settling. It is not classified
as steady-state idle. PostgreSQL container memory includes the shared local
instance and its pre-existing databases; only an isolated ASTRA database was
created and removed for the measurements.

### Frontend artifacts

| Artifact | Uncompressed | Gzip |
| --- | ---: | ---: |
| initial application chunk | 239,861 B | 60.40 KiB |
| React vendor chunk | 232,866 B | 74.50 KiB |
| application CSS | 118,852 B | 21.45 KiB |
| journey workspace chunk | 96,980 B | 27.02 KiB |
| Program 1 chunk | 34,995 B | 9.39 KiB |
| icons chunk | 26,278 B | 5.37 KiB |
| operations pages chunk | 14,369 B | 4.34 KiB |

All JavaScript and CSS files meet the file-size budgets. The generated HTML
currently emits module-preload links for every named chunk, including route
chunks. Increment D must verify the browser network behavior before claiming
that route-level lazy loading is effective.

## Measurement rules

1. Use a uniquely named PostgreSQL database and migrate it from an empty state.
2. Use only clearly synthetic data.
3. Record the exact command, sample size and authentication context.
4. Warm-up requests may be excluded only when the exclusion is documented.
5. Report failures and outliers; do not replace them with a preferred run.
6. Compare the same endpoint, data shape and host before and after a change.
7. Do not trade audit, RBAC, tenant scope, signed-record immutability or clinical
   validation for lower latency or fewer queries.
8. Remove every isolated measurement database and temporary seed after use.

## Current evidence-backed priorities

1. Reduce readiness latency without weakening its database check.
2. Instrument SQL counts for the critical read paths before changing queries.
3. Determine whether eager module-preload defeats route-level lazy loading.
4. Reduce repeated PostgreSQL fixture setup only if test isolation remains
   explicit and reliable.

No cache, worker, queue, search service or infrastructure split is justified by
the current measurements.
