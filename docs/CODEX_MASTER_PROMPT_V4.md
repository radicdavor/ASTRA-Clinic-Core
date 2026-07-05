# Codex master prompt v4 — Reliability First Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect and developer.

You are working on ASTRA Clinic Core, an open-source modular, API-first clinic operations platform.

The project already has a serious MVP foundation:

- FastAPI backend
- PostgreSQL
- Alembic workflow
- React + TypeScript frontend
- Docker Compose
- JWT auth
- permission-based RBAC
- scoped API keys for AI agents
- structured audit log
- appointment conflict validation
- inventory items, batches and stock movements
- FEFO consumption
- appointment material consumption service
- suppliers
- purchase orders and purchase order lines
- purchase receiving that creates inventory batches and stock movements
- invoices
- invoice lines
- draft invoice from appointment
- invoice issuing
- payment transactions

Your task is not to add broad new product features. Your task is to make the existing product trustworthy.

## Main rule

Stop feature sprawl.

Do not add new medical modules, new AI automations or cosmetic frontend changes until the existing domain logic is covered by tests and CI.

The next sprint is called:

**Reliability First Sprint**

The goal is to prove that the current workflows are correct.

## Phase 1 — Add backend test infrastructure

Add a proper backend test setup.

Tasks:

- Add pytest and required test dependencies.
- Add test database configuration.
- Add a clean test app/client fixture.
- Add isolated database fixture.
- Add fixtures for:
  - admin user
  - physician user
  - receptionist user
  - inventory manager user
  - billing user
  - AI API key
  - patient
  - provider
  - room
  - service
  - stock location
  - inventory item
  - inventory batch
  - supplier
- Add one command to run tests:
  - `make test`, or
  - documented `cd backend && pytest`

Important:

- Tests must not depend on manual seed data.
- Tests must not mutate the development database.
- Prefer PostgreSQL for integration tests. SQLite may hide transaction and locking issues.

Acceptance criteria:

- A developer can run all backend tests with one command.
- The first test proves `/health` works.
- The test database is isolated and repeatable.

## Phase 2 — Appointment and scheduling tests

Add tests for appointment correctness.

Required tests:

1. create appointment success
2. reject `end_time <= start_time`
3. reject invalid appointment status
4. reject invalid appointment source
5. reject provider overlap
6. reject room overlap
7. allow cancelled appointment not to block slot
8. allow no_show appointment not to block slot if this is intended behavior
9. update appointment validates conflicts
10. `/api/schedule/day` returns appointments ordered by start time
11. appointment create/update/delete creates structured audit records

Acceptance criteria:

- Scheduling bugs cannot silently reappear.
- A provider cannot be double-booked.
- A room cannot be double-booked.

## Phase 3 — RBAC and AI API key tests

Add tests for permission boundaries.

Required tests:

1. unauthenticated request returns 401
2. authenticated user without permission returns 403
3. admin can create API key
4. raw API key is returned only at creation
5. stored API key is hashed
6. AI API key with `ai.free_slots.read` can read free slots
7. AI API key without `inventory.adjust` cannot adjust stock
8. AI API key without `inventory.write_off` cannot write off stock
9. AI API key without `billing.mark_paid` cannot mark invoice paid
10. receptionist cannot write off stock
11. inventory manager cannot mark invoice paid
12. billing user cannot write off stock
13. audit log requires `audit.read`

Acceptance criteria:

- AI agent cannot perform destructive or financial actions unless explicitly scoped.
- Permission failures are clean 403 responses, not 500 errors.

## Phase 4 — Inventory ledger tests

Add tests for inventory correctness.

Required tests:

1. create inventory item
2. create batch
3. batch requires LOT when `lot_tracking_enabled=true`
4. batch requires expiration date when `expiration_tracking_enabled=true`
5. reject zero or negative quantity
6. FEFO consumes earliest expiration first
7. FEFO consumes null expiration batches last
8. insufficient stock fails before mutation
9. insufficient stock leaves all batch quantities unchanged
10. write-off requires reason
11. adjustment requires reason
12. transfer requires reason
13. transfer preserves total stock
14. transfer merges into existing target batch when item + lot + expiration + location + purchase_price + supplier match
15. recalculate stock fixes corrupted current_stock cache
16. low-stock endpoint returns items below reorder point
17. expiring endpoint returns batches within requested day window
18. stock movement audit is created

Acceptance criteria:

- `InventoryItem.current_stock` equals the sum of `InventoryBatch.quantity` after all operations.
- No operation can create negative stock.

## Phase 5 — Appointment material consumption tests

Test `backend/app/services/appointment_materials.py` and related endpoints.

Required tests:

1. suggested material consumption uses service material templates
2. required fixed quantity material is auto-consumed
3. required variable material must be explicitly provided
4. optional material is not auto-consumed unless provided
5. multiple lines for the same item are aggregated before stock validation
6. insufficient stock fails before any mutation
7. complete-with-consumption marks appointment completed only after successful consumption
8. failed consumption leaves appointment status unchanged
9. consumption creates stock movements
10. consumption audits InventoryItem and StockMovement changes

Acceptance criteria:

- Appointment completion and material consumption are atomic from the user’s perspective.
- Required variable materials such as propofol behave predictably.

## Phase 6 — Procurement tests

Test purchase order and receiving workflow.

Required tests:

1. create purchase order
2. add purchase order line
3. update purchase order line
4. delete purchase order line only while allowed
5. purchase order total recalculates from lines
6. partial receive creates InventoryBatch
7. partial receive creates StockMovement purchase_receipt
8. partial receive updates `quantity_received`
9. partial receive sets order status to `partially_received`
10. full receive sets order status to `received`
11. reject over-receive
12. require LOT/expiration on receive when tracking is enabled
13. receiving multiple lines is atomic: if one line fails, no batches or movements are created
14. receiving updates current stock cache
15. purchase receiving is audited

Acceptance criteria:

- Purchase receiving is reliable enough to be used for real stock entry later.

## Phase 7 — Billing tests

Test invoice and payment workflow.

Required tests:

1. draft invoice from appointment
2. draft invoice includes service line
3. repeated draft from same appointment returns existing invoice and does not duplicate
4. add invoice line while invoice is draft
5. update invoice line while invoice is draft
6. delete invoice line while invoice is draft
7. issue invoice generates official invoice number
8. cannot edit invoice lines after issue
9. record partial payment
10. record final payment
11. reject payment above total amount
12. mark-paid requires `billing.mark_paid`
13. cannot cancel paid invoice in MVP workflow
14. invoice total is recalculated correctly
15. payment_status is recalculated correctly
16. invoice/payment events are audited

Acceptance criteria:

- Billing state transitions are deterministic.
- PaymentTransaction remains the payment history source of truth.

## Phase 8 — Audit tests

Audit is a medical/legal feature, not a nice-to-have.

Required tests:

1. patient update includes before_json and after_json
2. appointment update includes before_json and after_json
3. inventory item update includes before_json and after_json
4. inventory batch creation is audited
5. stock write-off includes reason
6. stock transfer is audited
7. purchase order receive audits created batch and movement
8. invoice issue is audited
9. payment transaction is audited
10. API key actor appears as `api_key`, not `user` or `system`
11. audit log filtering works for entity_type/action/actor_type

Acceptance criteria:

- Critical mutations can be reconstructed from audit data.

## Phase 9 — Transaction rollback tests

Add explicit rollback tests. These are high-value tests.

Required tests:

1. appointment complete-with-consumption fails if stock is insufficient and appointment remains not completed
2. failed appointment material consumption does not create partial stock movements
3. purchase receive with two valid lines and one invalid line creates no batches and no movements
4. invoice payment above total creates no payment and does not change invoice status
5. stock transfer failure leaves source batch unchanged
6. stock write-off failure leaves batch unchanged

Acceptance criteria:

- Multi-step operations are atomic.
- Partial state corruption is prevented.

## Phase 10 — Add CI baseline

Add GitHub Actions workflow.

File:

`.github/workflows/ci.yml`

Workflow should run on:

- push
- pull_request

Jobs:

### Backend job

- checkout
- setup Python
- install backend dependencies
- run lint if already configured, otherwise skip with TODO
- run pytest

### Frontend job

- checkout
- setup Node
- install frontend dependencies
- run TypeScript check if configured
- run frontend build

### Optional integration job

- start PostgreSQL service
- run Alembic migrations
- run backend tests against PostgreSQL

Acceptance criteria:

- CI fails if backend tests fail.
- CI fails if frontend build fails.
- README documents how to run tests locally.

## Phase 11 — OpenAPI contract hardening

Stabilize API contracts.

Tasks:

- Add response_model to remaining important routes.
- Avoid returning raw SQLAlchemy models where sensitive fields may leak.
- Add `ErrorResponse` schema.
- Add examples to key request schemas.
- Confirm that password_hash is never returned.
- Confirm that API key hash is never returned.
- Confirm that raw API key is shown only once on creation.

Priority routes:

- auth login
- API key creation/listing
- patients
- appointments
- schedule/day
- AI free-slots
- inventory
- purchase orders
- invoices
- audit log

Acceptance criteria:

- `/docs` can be used by an external integrator or AI agent as a reliable contract.

## Phase 12 — Fiscalization adapter stub

Do not implement real Croatian fiscalization yet.

Create architecture boundary only.

Add:

`backend/app/services/fiscalization.py`

Required elements:

- `FiscalizationResult`
- `FiscalizationProvider`
- `NoopFiscalizationProvider`
- `CroatiaFiscalizationProviderStub`

Behavior:

- Invoice issue can optionally call a fiscalization provider.
- Default provider is Noop.
- Noop returns `not_configured`.
- Stub does not call any external service.
- Fiscalization attempt is audited.
- Store status/reference if fields exist.

Acceptance criteria:

- Future Croatian fiscalization can be plugged in without rewriting invoice issuing.
- Local development stays offline and safe.

## Phase 13 — Production hardening basics

Add minimal production discipline.

Tasks:

- Add `SECURITY.md`.
- Add `docs/DEPLOYMENT_GOOGLE_CLOUD.md`.
- Add `docs/BACKUP_RESTORE.md`.
- Add `scripts/backup_postgres.sh`.
- Add clear production env var documentation.
- Add environment mode, for example `APP_ENV=development|production`.
- Fail startup in production if `JWT_SECRET` is default/weak.
- Configure token expiration.
- Add CORS per environment.
- Add TODO or simple implementation for login rate limiting.

Acceptance criteria:

- No one can accidentally deploy production with local development secrets.
- Backup and restore path is documented.

## Phase 14 — Frontend operational workflows

Only after backend tests and CI are green.

Add or improve UI for:

- receive purchase order lines
- show ordered/received/remaining quantities
- stock transfer with mandatory reason
- write-off with mandatory reason
- appointment completion with material consumption
- invoice draft from appointment
- issue invoice
- record payment
- audit filters
- API key management

Acceptance criteria:

- A clinic user can execute the daily workflows without curl.
- Dangerous actions require confirmation.
- Frontend validation mirrors backend validation.

## Phase 15 — Module manifest foundation

Only after reliability work.

Add safe manifest-based modularity.

Directory structure:

```text
backend/app/modules/catalog/
  gastroenterology/
    module.json
    services.json
    material_templates.json
    workflows.json
    patient_instructions.json
    ai_prompts.json
```

Initial module manifests:

- gastroenterology
- endoscopy
- dermatology_aesthetics
- colonoscopy_prep
- h_pylori
- sibo_imo
- mounjaro

Rules:

- Manifests are data/config.
- Do not execute arbitrary plugin code.
- Loading modules must be idempotent.
- Adding a module should not require core model changes.

Acceptance criteria:

- Services and material templates can be loaded from module manifests.
- Module API exposes installed modules and their services.

## Suggested commit sequence

1. `test: add backend pytest infrastructure`
2. `test: cover appointment scheduling rules`
3. `test: cover rbac and ai api key boundaries`
4. `test: cover inventory ledger and fefo behavior`
5. `test: cover appointment material consumption workflow`
6. `test: cover purchase receiving workflow`
7. `test: cover billing invoice and payment workflow`
8. `test: cover audit before after snapshots`
9. `test: cover transaction rollback behavior`
10. `ci: add backend and frontend workflow`
11. `docs: harden openapi schemas and examples`
12. `feat: add fiscalization provider stub`
13. `chore: add security deployment and backup documentation`
14. `feat: add frontend operational workflows`
15. `feat: add module manifest loader foundation`

## Definition of done

This sprint is complete only when:

- backend tests exist and pass
- CI runs on push and pull request
- appointment, RBAC, inventory, procurement, billing and audit are covered
- transaction rollback behavior is covered
- OpenAPI no longer exposes sensitive internals
- fiscalization boundary exists as a stub
- production hardening docs exist
- README explains test and CI workflow

Do not proceed to broad new feature work until this is complete.
