# Role and information architecture closure test map

Measured baseline: 23 July 2026

Branch: `ux/information-architecture-simplification`

This map records the executable technical gates for the demo persona and
information-architecture closure. It does not authorize production use or
real patient data.

## Commands

| Layer | Command | Purpose |
| --- | --- | --- |
| Backend fast | `python scripts/run_test_gate.py fast` | Short contract and domain feedback |
| Backend full | `cd backend && python -X faulthandler -m pytest -ra -vv --durations=100` | Complete backend suite with slow-test evidence |
| PostgreSQL integration | `python scripts/run_test_gate.py integration` with `TEST_DATABASE_URL` | PostgreSQL-only behavior |
| Frontend unit | `cd frontend && npm test -- --run` | Components, role navigation and interaction contracts |
| Program 2 contract | Included in the frontend Vitest run | Static Program 2 safety contracts |
| Route-mocked browser | `cd frontend && npm run e2e` | Browser navigation against controlled route fixtures |
| DB-backed browser | `cd frontend && npm run e2e:db` | Isolated database, backend, frontend and Chromium workflow |
| Pilot smoke | `cd frontend && npm run smoke` | Browser-level semantic role and navigation contracts |
| Human usability preflight | `cd frontend && npm run usability:preflight` | Isolated five-persona session startup and deterministic seed |
| Human usability session | `cd frontend && npm run usability:session` | Moderated synthetic evaluation runner; not automated usability evidence |
| TypeScript | `cd frontend && npm run typecheck` | Type contract |
| Build | `cd frontend && npm run build` | Production frontend bundle |
| OpenAPI | `backend/.localrun-venv/Scripts/python.exe scripts/generate_openapi_types.py --check` | Generated frontend API types |
| Alembic | `cd backend && alembic heads`, empty-database `alembic upgrade head` | One head and installability |
| Development Compose | `docker compose config --quiet` | Development configuration |
| Production Compose | `docker compose --env-file <ignored synthetic env> -f docker-compose.prod.example.yml config` | Fail-closed production contract |

## Baseline findings

- The original full backend suite was not hanging. It completed 794 collected
  tests in 10 minutes 44 seconds when allowed to finish. The final suite
  contains more tests and is measured separately in the closure report.
- The former 10-minute external command limit stopped the suite shortly before
  completion and therefore misclassified a long-running suite as a timeout.
- The completed baseline exposed one genuine fail-closed registry failure:
  the operational invoice projection added on this branch changed the reviewed
  `/api` route count from 260 to 261.
- DB-backed Playwright uses dedicated ports and a dedicated database, but the
  original runner lacked phase-specific diagnostics, a test-run identity
  handshake and robust awaited process termination.
- The historical source-fragment smoke test has been replaced by five
  browser-level semantic persona contracts.

## Closure evidence rules

- A timeout is not reported as a pass.
- A skipped PostgreSQL test is not PostgreSQL evidence.
- Browser role hiding is not backend authorization evidence.
- Human usability is recorded only after a separately run human session.
- Test artifacts must contain synthetic data only and remain ignored locally.

## Final measured result

The final commands and measured counts are recorded in
[role-ia-technical-closure.md](role-ia-technical-closure.md). The repository
gate is complete for a local synthetic candidate; human usability remains
unperformed.
