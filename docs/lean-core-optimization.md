# Module 3.5 Lean Core optimization

Status: complete for the authorized local synthetic validation scope

Measured: 22 July 2026

## Outcome

ASTRA remains a React application, one FastAPI process and PostgreSQL. No Redis,
Celery, queue, scheduler, search service or additional application process was
introduced. The production frontend is served by Nginx, so the minimal deployed
process set remains PostgreSQL + FastAPI + Nginx (3 -> 3 processes).

The work reduced policy duplication, SQL statements on critical reads, eager
frontend code and request waterfalls. It also removed migrations and seed work
from production API startup. Security and clinical behavior were not traded for
speed.

## Architecture and authorization

- Clinical-record and clinic-scope capabilities now use shared policies instead
  of route-local role checks.
- Institution reads, own-draft editing, source access and signed-report access
  retain immediate membership and permission evaluation; there is no long-lived
  authorization cache.
- Revoked sessions, CSRF, source classification, author-only editing, signed
  immutability, addendum integrity, appointment concurrency, audit and billing
  isolation remain covered by the full PostgreSQL and browser gates.
- The policy inventory and ownership map are in
  `docs/lean-core-authorization-map.md`.

## Backend projections and SQL

Counts include shared authentication and access-audit SQL. Endpoint-only work
is documented in `docs/lean-core-query-analysis.md`.

| Request | Before | After |
| --- | ---: | ---: |
| current browser session | 4 | 4 |
| daily dashboard | 12 | 11 |
| patient directory | 8 | 7 |
| patient appointment availability | 9 | 8 |
| patient invoice/payment projection | 11 | 10 |
| institution clinical record | 16 | 11 |
| signed report detail | 15 | 11 |

The clinical-record list now selects metadata rather than full document text,
OCR or AI summary content. A regression test inspects executed SQL. Existing
indexes produced acceptable plans at 20,000 patients and 200,000 documents, so
no speculative index or migration was added. Critical list paths remain bounded.

Final synthetic response sizes were 3,082 B for dashboard, 1,060 B for patient
directory, 853 B for institution clinical record and 568 B for signed-report
detail.

## Endpoint benchmark

Both samples used 20 warm authenticated requests, PostgreSQL, browser sessions,
clinic headers and synthetic data on the same host. The final late-run sample
was materially slower on DB-backed reads; therefore only `/ready` supports an
evidence-backed latency improvement claim.

| Endpoint | Baseline p50 / p95 | Final p50 / p95 | Final budget |
| --- | ---: | ---: | --- |
| `/health` | 5.85 / 6.76 ms | 8.19 / 9.88 ms | pass |
| `/ready` | 359.96 / 524.98 ms | 58.63 / 139.89 ms | pass; p95 improved 73% |
| dashboard | 77.70 / 120.30 ms | 272.92 / 1,083.69 ms | fail in final sample |
| patient directory | 41.92 / 58.77 ms | 180.19 / 363.93 ms | fail in final sample |
| clinical record | 69.83 / 194.28 ms | 326.77 / 616.18 ms | fail in final sample |
| signed report | 60.46 / 172.08 ms | 335.41 / 693.85 ms | fail in final sample |

The SQL-count reductions are deterministic regression guards. The final latency
sample is not used to claim improvement for the four failed rows. Production
capacity decisions require repeatable measurements on a controlled host rather
than a developer workstation after the full validation workload.

## Frontend

| Measurement | Before | After |
| --- | ---: | ---: |
| entry JavaScript | 239,861 B | 63,861 B |
| journey workspace chunk | 96,980 B, preloaded | 73,709 B, route-loaded |
| workspace requests, documents entry | 16 | 9 |
| workspace requests, encounter entry | 16 | 8 |
| final CSS | 118,852 B | 118,852 B |

Routes are lazy-loaded and the emitted HTML preloads only React and icons.
Superseded API reads are aborted and stale results are ignored, including after
clinic/date/patient changes. The dashboard retains its compact projection.
There is no high-frequency polling; the remaining timers are one-shot UI timers.

## Runtime resources

| Measurement | Baseline | Final |
| --- | ---: | ---: |
| backend process to readiness | 12.37 s | 16.91 s |
| uvicorn working set | 209.2 MiB | 181.38 MiB |
| backend idle CPU over 10 s | 0 ms | 0 ms |
| frontend preview startup | 1.38 s | 2.84 s |
| frontend preview working set | 66.6 MiB | 72.57 MiB |
| frontend preview idle CPU over 5 s | 62.5 ms | 0 ms |
| PostgreSQL container sample | 172-179 MiB | 201.2 MiB |

The startup and PostgreSQL samples did not improve and are reported as such.
Fifty repeated signed-report reads changed the true uvicorn working set from
191.68 MiB to 191.74 MiB (+0.07 MiB), which found no unbounded growth in this
small smoke. This is not a long-duration load or leak test.

Production startup no longer migrates or seeds. Schema status and expired
session cleanup are bounded CLI commands intended for deployment automation or
cron/Task Scheduler, never resident loops. See
`docs/lean-core-runtime-and-maintenance.md`.

## Test and build results

| Gate | Final result | Time |
| --- | --- | ---: |
| backend fast | 145 passed | 9.50 s final pytest; 19.23 s earlier wall sample |
| PostgreSQL integration | 16 passed | 64.08 s pytest / 83.43 s with migration |
| backend full | 687 passed, 1 Windows skip | 762.09 s pytest / 789.23 s with migration |
| `npm ci` | passed, 0 vulnerabilities | 37.90 s |
| frontend typecheck | passed | 27.84 s |
| frontend unit/contract | 57 + 4 passed | 37.38 s |
| frontend smoke | passed | 3.68 s |
| frontend build | passed | 52.15 s |
| route-mocked Playwright | 1 passed | 15.7 s final; 19.10 s earlier wall sample |
| DB-backed Playwright | 10 passed | 58.8 s / 142.37 s full orchestration |
| OpenAPI drift | passed | 10.81 s |

The full backend pytest time increased from 710.93 s to 762.09 s while the suite
grew from 681 to 688 collected tests; no full-suite speedup is claimed. The fast
gate provides the short local feedback loop without removing full coverage.

## Validation and known limitations

- Empty PostgreSQL upgrade, downgrade to `0060`, and re-upgrade to the single
  `0062` head passed.
- Alembic's optional `check` command reports historical ORM/migration metadata
  drift across many older indexes and constraints. It is not an existing CI
  gate. Auto-generating a large corrective migration would be unsafe and is
  outside this optimization scope.
- Development and production-example Compose configurations parse. DB-backed
  E2E has a dedicated orchestrator rather than a separate Compose file.
- The existing `python-jose` UTC deprecation warnings remain.
- Backup/restore and recovery remain reserved for Module 4.
- No real patient data, production deployment or live provider was used.

## Decision

`MODULE 3.5 COMPLETE — READY FOR MODULE 4`

Module 4 is not started by this work.
