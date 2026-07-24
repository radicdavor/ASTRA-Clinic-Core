# ASTRA test strategy

## Goals

The local feedback loop must be quick without replacing PostgreSQL, browser or
full-suite coverage. Test acceleration is achieved by ordering and removing CI
duplication, never by deleting assertions or weakening safety expectations.

## Layers

### Backend fast

```bash
python scripts/run_test_gate.py fast
# or: make backend-fast
```

The manifest contains 145 policy, schema, selector and contract tests that do
not require the PostgreSQL integration directory. Measured locally:

- pytest time: 8.01 s;
- process wall time: 19.23 s;
- result: 145 passed after adding the gate's own regression tests.

A final rerun also passed all 145 tests in 9.50 s of pytest time.

The explicit manifest is intentional: `pytest -m "not integration"` is the full
backend core, not a fast gate, and took roughly the same order of time as the
historical 710.93-second full baseline. New tests enter the fast manifest only
when they remain deterministic and database-independent.

### Backend PostgreSQL integration

```bash
TEST_DATABASE_URL=postgresql+psycopg://... \
ASTRA_REQUIRE_TEST_DATABASE=true \
python scripts/run_test_gate.py integration
# or: make backend-integration
```

This layer owns real PostgreSQL behavior: concurrency locks, institution/clinic
authorization against the database, domain workflows, migrations exercised by
the setup and production-like API projections. On a freshly created and fully
migrated local database it produced:

- migration plus integration wall time: 83.43 s;
- pytest time: 64.08 s;
- result: 16 passed.

Integration tests retain the `integration` pytest marker and are never replaced
with SQLite or mocks in this gate.

### Backend full

```bash
python scripts/run_test_gate.py full
# or: make backend-full
```

The full layer runs `pytest -ra --durations=50`. The Module 3.5 baseline was 681
passed in 710.93 s before the optimization commits. It remains the authoritative
backend regression gate and reports the slowest 50 tests.

The final isolated PostgreSQL run collected 688 tests and produced 687 passed,
one POSIX-entrypoint skip on Windows and 982 warnings in 762.09 s (789.23 s
including empty-database migration). The suite grew by seven collected tests;
no full-suite speed improvement is claimed.

### Frontend component and contract

```bash
cd frontend
npm run typecheck
npm test -- --run
# or: make frontend-test
```

This runs TypeScript validation, Program 2 source contracts and all Vitest
component/unit tests. It does not substitute for browser E2E.

### Browser E2E smoke

```bash
cd frontend
npm run e2e
# or: make e2e-smoke
```

The route-mocked Playwright scenario checks the dashboard-native reception and
canonical clinical workspace quickly. It is a browser/UI smoke layer, not a
database authorization proof.

Final rerun: one passed in 15.7 s. An earlier successful rerun took 15.4 s
(19.10 s process wall). The mock explicitly returns
the real 404 contract for an unopened activity form and an array for the
intervention collection; a generic successful object is not a valid substitute.

### DB-backed E2E full

```bash
cd frontend
npm run e2e:db
# or: make e2e-full
```

The orchestrator creates a uniquely named PostgreSQL database, migrates it once,
seeds only the required synthetic scenario, starts one backend and one frontend,
runs the full Playwright suite, terminates both processes and drops the database.
Its migration, seed and server setup are session-scoped to that run rather than
repeated per scenario.

Final result: 10 passed in 58.8 s, with 142.37 s total orchestration time.

### Recovery

Backup/restore and recovery validation remain reserved for Module 4. The current
CI backup/restore safety script is preserved; this module does not expand that
scope.

## CI ordering

The backend job now runs:

1. dependency installation and OpenAPI drift check;
2. migration upgrade/downgrade/re-upgrade;
3. fast feedback gate;
4. all non-integration backend tests once;
5. all PostgreSQL integration tests once;
6. the existing synthetic backup/restore validation.

Previously snapshot and advisory suites ran explicitly and then ran again inside
the full backend suite, while integration tests also ran inside full pytest and
again as an explicit gate. The new ordering preserves every collected test but
removes those duplicate CI executions. The small fast manifest intentionally
overlaps the later core run to provide early feedback.

## Isolation rules

- Never share mutable state between tests to save time.
- Never remove migration, concurrency, signed-report, addendum, classification,
  session/CSRF, audit or authorization coverage from the full gates.
- PostgreSQL integration uses an isolated database and explicit safety guard.
- DB-backed E2E uses synthetic data only and always attempts teardown.
- Do not add fixed sleeps where readiness polling with a deadline is available.

## PR #3 scope-remediation gate

The security gate additionally includes explicit active-clinic billing denial,
institution clinical-child denial, PHI-safe audit projection, tenant-bound
API-key tests, and populated `0063 -> 0066` migration fixtures. Legacy tests
must create realistic clinic memberships and object provenance; tests may not
bypass production scope rules by using unscoped users, rooms, invoices, or API
keys.
