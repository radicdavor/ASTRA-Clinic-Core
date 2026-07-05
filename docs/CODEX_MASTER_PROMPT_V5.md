# Codex master prompt v5 — Quality Gate Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect and developer.

ASTRA Clinic Core has implemented v4: tests, CI, fiscalization stub, security docs, deployment docs and backup docs now exist.

Do not add broad new product features yet.

The next sprint is:

**Quality Gate Sprint**

The goal is to make the existing tests and infrastructure representative of real production risks.

## Current known state

The repository now includes:

- `.github/workflows/ci.yml`
- backend pytest tests
- appointment tests
- inventory tests
- procurement tests
- billing tests
- appointment material consumption rollback test
- fiscalization provider stub
- `SECURITY.md`
- `docs/DEPLOYMENT_GOOGLE_CLOUD.md`
- `docs/BACKUP_RESTORE.md`

This is good, but not enough.

Main concern:

Tests appear to use SQLite fixtures while CI provisions PostgreSQL. This means critical PostgreSQL-specific behavior is not fully tested:

- Alembic migrations
- row locking
- `with_for_update()`
- constraints
- transaction rollback
- PostgreSQL type behavior

## Main rule

Do not broaden feature scope until the quality gate passes.

No new medical modules.
No new AI automations.
No cosmetic frontend work.

First prove that the current backend is correct under realistic conditions.

## Phase 1 — Split unit tests and PostgreSQL integration tests

Add a clear test strategy.

Tasks:

- Keep fast SQLite tests for pure service/unit behavior if useful.
- Add PostgreSQL integration tests for domain workflows.
- Add environment variable:
  - `TEST_DATABASE_URL`
- In CI, use PostgreSQL service and set `TEST_DATABASE_URL=postgresql+psycopg://astra:astra@localhost:5432/astra_ci`.
- Ensure PostgreSQL integration tests run in CI.
- Document test modes in README.

Suggested structure:

```text
backend/tests/unit/
backend/tests/integration/
```

or:

```text
backend/tests/test_*.py
backend/tests/integration/test_*.py
```

Acceptance criteria:

- Unit tests can run quickly.
- Integration tests use PostgreSQL.
- CI fails if PostgreSQL integration tests fail.

## Phase 2 — Migration smoke test

Add a test or CI step proving migrations work.

Tasks:

- Start with an empty PostgreSQL database.
- Run `alembic upgrade head`.
- Verify key tables exist:
  - users
  - roles
  - permissions
  - patients
  - appointments
  - inventory_items
  - inventory_batches
  - stock_movements
  - purchase_orders
  - invoices
  - audit_logs
- Optionally run seed idempotency test.

Acceptance criteria:

- CI proves migrations can build the database from zero.
- Seed does not duplicate core data.

## Phase 3 — API-level permission tests

Current service tests are useful, but not enough.

Add HTTP API tests through FastAPI TestClient or httpx.

Required tests:

1. unauthenticated patient list returns 401
2. limited user without `inventory.adjust` cannot call `/api/inventory/adjustment`
3. limited user without `inventory.write_off` cannot call `/api/inventory/write-off`
4. limited user without `billing.mark_paid` cannot mark invoice paid
5. user without `audit.read` cannot read `/api/audit-log`
6. admin can create an API key
7. API key is returned raw only once
8. API key hash is not returned in list responses
9. API key with only AI scopes cannot write off stock
10. API key with only AI scopes cannot mark invoice paid
11. API key actor is recorded correctly in audit when it performs an allowed action

Acceptance criteria:

- Permission boundaries are tested at the HTTP layer.
- AI key cannot perform destructive or financial operations.

## Phase 4 — API-level appointment tests

Add endpoint tests for scheduling.

Required tests:

1. POST `/api/appointments` success
2. POST overlapping provider appointment returns 409
3. POST overlapping room appointment returns 409
4. PATCH appointment revalidates overlap
5. invalid status returns 422
6. invalid source returns 422
7. cancelled appointment does not block slot
8. `/api/schedule/day` returns ordered results
9. audit record is created on create/update/delete

Acceptance criteria:

- Scheduling correctness is proven through the actual API path.

## Phase 5 — API-level inventory workflow tests

Add PostgreSQL-backed integration tests for inventory endpoints.

Required tests:

1. create inventory item
2. create batch with LOT/expiration validation
3. write-off requires reason
4. adjustment requires reason
5. transfer requires reason
6. transfer preserves total stock
7. transfer merges into existing target batch
8. FEFO endpoint/workflow consumes earliest expiration first if exposed through endpoint
9. recalculate stock endpoint repairs corrupted cache
10. low-stock endpoint works
11. expiring endpoint works
12. stock movements are audit logged

Acceptance criteria:

- Inventory workflow is proven through API and PostgreSQL.

## Phase 6 — API-level appointment material consumption tests

Test complete-with-consumption through the endpoint.

Required tests:

1. fixed required material is consumed
2. variable required material must be provided
3. optional material is not consumed unless provided
4. insufficient stock returns 409
5. insufficient stock leaves appointment status unchanged
6. insufficient stock creates no partial stock movements
7. successful completion changes appointment status to completed
8. successful completion creates stock movements
9. successful completion audits InventoryItem and StockMovement
10. multiple lines for same inventory item are aggregated before mutation

Acceptance criteria:

- Appointment completion and material consumption are atomic through the real endpoint.

## Phase 7 — API-level procurement tests

Test purchase order receiving through endpoint.

Required tests:

1. create purchase order
2. add purchase order line
3. partial receive through endpoint
4. partial receive creates batch
5. partial receive creates movement
6. partial receive updates current stock
7. partial receive updates line quantity_received
8. full receive sets status received
9. over-receive returns 409
10. missing LOT/expiration returns 422 when tracking enabled
11. receive request with one invalid line creates no batches and no movements
12. receive action is audited

Acceptance criteria:

- Procurement workflow is trustworthy through HTTP API, not only service functions.

## Phase 8 — API-level billing tests

Test invoice workflow through endpoint.

Required tests:

1. draft invoice from appointment endpoint
2. repeated draft does not duplicate invoice
3. add invoice line endpoint
4. issue invoice endpoint
5. official invoice number assigned on issue
6. line editing after issue is blocked
7. record partial payment endpoint
8. record final payment endpoint
9. overpayment returns 409
10. mark-paid requires permission
11. invoice/payment actions are audited
12. fiscalization provider is called or explicitly skipped by Noop during issue workflow

Acceptance criteria:

- Billing workflow is proven through the API.

## Phase 9 — Audit quality tests

Audit must be reconstructable.

Required tests:

1. update patient has before_json and after_json
2. update appointment has before_json and after_json
3. inventory write-off has before_json/after_json and reason
4. stock transfer creates audit records for batch and movements
5. purchase receive audits created batch and movement
6. invoice issue audits before/after
7. payment transaction audit exists
8. API key action has actor_type `api_key`
9. request_id is stored when available
10. audit filtering by entity_type/action/actor_type works

Acceptance criteria:

- Critical mutations can be reconstructed from audit log.

## Phase 10 — Fiscalization stub integration

Fiscalization stub exists, but it must be integrated cleanly.

Tasks:

- Ensure invoice issuing workflow can call fiscalization provider.
- Default provider must be `NoopFiscalizationProvider`.
- Noop provider must not call external services.
- Store fiscalization status/reference/message if model fields exist.
- If model fields do not exist, add migration for:
  - fiscalization_status
  - fiscalization_provider
  - fiscalization_reference
  - fiscalization_message
  - fiscalized_at
- Audit fiscalization attempts.
- Add tests for Noop provider behavior.

Acceptance criteria:

- Invoice issue can pass through fiscalization boundary without external calls.
- Future Croatian fiscalization can be implemented without changing billing API.

## Phase 11 — CI hardening

Improve `.github/workflows/ci.yml`.

Tasks:

- Ensure backend tests use PostgreSQL for integration tests.
- Add separate unit and integration test commands if useful.
- Add frontend typecheck if package supports it.
- Add frontend lint if package supports it.
- Add dependency caching for Python if appropriate.
- Upload test logs on failure if useful.
- Add CI badge to README.

Acceptance criteria:

- CI proves backend migrations, backend tests and frontend build.
- CI fails on integration test failure.

## Phase 12 — Production hardening enforcement

Docs exist, now enforce the most important rule.

Tasks:

- Add `APP_ENV` config.
- Fail startup in production if JWT secret is default, missing or weak.
- Fail startup in production if CORS allows localhost or wildcard.
- Add access token expiration config and tests.
- Add README section for production safety checks.

Acceptance criteria:

- Accidental production deployment with local secrets is blocked.

## Phase 13 — Frontend operational gap review

Do not build all UI blindly. First audit current frontend.

Create document:

`docs/FRONTEND_OPERATIONAL_GAP_ANALYSIS.md`

Assess whether UI supports:

- purchase order receive by line
- ordered/received/remaining display
- stock transfer with mandatory reason
- write-off with mandatory reason
- complete appointment with material consumption
- draft invoice from appointment
- issue invoice
- record payment
- audit filters
- API key management

Then implement the top 3 missing workflows only.

Recommended top 3:

1. complete appointment with material consumption
2. purchase order receiving
3. invoice issue and payment

Acceptance criteria:

- Most clinically relevant daily workflows can be done without curl.

## Phase 14 — Module manifest foundation, only after quality gate

Add minimal manifest loader only if tests and CI remain green.

Do not execute arbitrary plugin code.

Add data-only manifests:

```text
backend/app/modules/catalog/gastroenterology/module.json
backend/app/modules/catalog/gastroenterology/services.json
backend/app/modules/catalog/gastroenterology/material_templates.json
```

Initial module examples:

- gastroenterology
- endoscopy
- dermatology_aesthetics

Acceptance criteria:

- Module loader imports services/material templates idempotently.
- Adding a module does not require core model changes.

## Suggested commit sequence

1. `test: add postgresql integration test setup`
2. `test: add migration smoke tests`
3. `test: cover api permission boundaries`
4. `test: cover appointment api scheduling rules`
5. `test: cover inventory api workflows`
6. `test: cover appointment material consumption api workflow`
7. `test: cover procurement api receiving workflow`
8. `test: cover billing api workflow`
9. `test: cover audit reconstruction and api key actor`
10. `feat: integrate noop fiscalization into invoice issue workflow`
11. `ci: harden postgres integration tests and frontend checks`
12. `chore: enforce production secret and cors safety checks`
13. `docs: add frontend operational gap analysis`
14. `feat: add top frontend operational workflows`
15. `feat: add safe module manifest loader foundation`

## Definition of done

Quality Gate Sprint is done when:

- PostgreSQL integration tests run in CI
- migration smoke test passes in CI
- API permission boundaries are tested
- AI API key limits are tested
- appointment/inventory/procurement/billing workflows are tested through API
- audit reconstruction is tested
- rollback behavior is tested through endpoints
- fiscalization stub is integrated into invoice issue workflow
- production weak-secret/CORS checks are enforced
- frontend gap analysis exists
- top 3 operational UI gaps are addressed

Do not start broader AI automation or new medical modules before this is complete.
