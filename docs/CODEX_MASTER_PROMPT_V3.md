# Codex master prompt v3 — ASTRA Clinic Core testing, CI and hardening sprint

Use this prompt in Codex for the next development sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect and developer.

You are continuing ASTRA Clinic Core, an open-source modular, API-first clinic operations platform.

The project is no longer just a scaffold. It now has meaningful backend logic for:

- patients
- appointments
- appointment conflict validation
- RBAC permissions
- scoped API keys for AI agents
- structured audit
- inventory items
- batches and FEFO consumption
- stock transfers
- suppliers
- purchase orders and purchase order lines
- purchase receiving that creates inventory batches and stock movements
- invoices
- invoice lines
- invoice draft from appointment
- invoice issuing
- payment transactions

Your task is now to stop feature sprawl and stabilize the system.

## Main sprint objective

Build confidence.

Do not add new medical modules yet. Do not add cosmetic UI features first. The next sprint must make the project testable, safer, and harder to break.

Focus on:

1. backend test suite
2. CI baseline
3. OpenAPI schema stabilization
4. transaction/rollback correctness
5. fiscalization adapter stub
6. production hardening basics
7. frontend operational gaps only after backend tests pass

## Strategic rule

ASTRA Clinic Core must remain a clinic operating system, not a bloated EMR and not a giant ERP.

The core workflows are:

- schedule patient
- manage daily flow
- consume material based on service
- order stock
- receive stock
- invoice appointment
- track payment
- audit all critical changes
- allow AI agent only within strict scopes

## Phase 1 — add backend test infrastructure

Add pytest infrastructure for backend.

Tasks:

- Add pytest dependencies.
- Add test database configuration.
- Add fixtures for:
  - database session
  - test client
  - admin user
  - physician user
  - receptionist user
  - inventory manager user
  - billing user
  - AI API key
  - patient
  - provider
  - room
  - services
  - inventory item
  - stock location
- Tests must run isolated and repeatably.
- Prefer PostgreSQL test service if practical; if using SQLite for speed, be careful because locking/check constraints may differ. For inventory concurrency/transaction tests, prefer PostgreSQL.

Add command:

```bash
make test
```

or document:

```bash
cd backend && pytest
```

Acceptance criteria:

- Test suite runs with one command.
- Tests do not require manual seed data.
- Tests do not modify development database.

## Phase 2 — appointment tests

Add tests for appointment correctness.

Required tests:

1. create appointment success
2. reject end_time <= start_time
3. reject invalid appointment status
4. reject invalid appointment source
5. reject provider overlap
6. reject room overlap
7. allow cancelled appointment not to block slot
8. allow no_show appointment not to block slot if configured as non-blocking
9. schedule/day returns appointments ordered by start_time
10. audit log is created for appointment create/update/delete

Acceptance criteria:

- Conflict validation cannot regress silently.
- Update appointment also checks conflicts.

## Phase 3 — RBAC and AI API key tests

Add tests for permission boundaries.

Required tests:

1. unauthenticated request is rejected
2. user without permission is rejected
3. admin can create API key
4. API key is stored hashed, raw key returned only once
5. AI API key with `ai.free_slots.read` can read free slots
6. AI API key without `inventory.adjust` cannot adjust stock
7. AI API key without `billing.mark_paid` cannot mark invoice paid
8. receptionist cannot write off stock
9. inventory manager cannot mark invoice paid
10. billing user cannot write off stock

Acceptance criteria:

- AI agent cannot perform destructive or financial actions unless explicitly scoped.
- Sensitive operations fail with 403, not 500.

## Phase 4 — inventory ledger tests

Add tests for inventory correctness.

Required tests:

1. create item
2. create batch
3. batch requires LOT if lot_tracking_enabled
4. batch requires expiration_date if expiration_tracking_enabled
5. FEFO consumes earliest expiration first
6. FEFO skips null expiration until later
7. insufficient stock rolls back and leaves all batch quantities unchanged
8. write-off requires reason
9. adjustment requires reason
10. transfer requires reason
11. transfer preserves total stock
12. transfer merges into existing target batch when item + lot + expiration + location + purchase_price + supplier match
13. recalculate stock fixes corrupted current_stock cache
14. low-stock endpoint returns items below reorder point
15. expiring endpoint returns batches within requested days

Acceptance criteria:

- InventoryItem.current_stock always matches sum of InventoryBatch.quantity after operations.
- No operation can create negative quantity.

## Phase 5 — procurement tests

Add tests for purchase order workflow.

Required tests:

1. create purchase order
2. add purchase order line
3. update purchase order line
4. delete purchase order line only while allowed
5. recalculate PO total
6. partial receive creates InventoryBatch
7. partial receive creates StockMovement purchase_receipt
8. partial receive updates quantity_received
9. partial receive sets status partially_received
10. full receive sets status received
11. reject over-receive
12. require LOT/expiration on receive when item tracking requires it
13. receiving multiple lines is atomic: if one line fails, no batches are created

Acceptance criteria:

- Purchase receiving is trustworthy.
- PO status is derived from line state.

## Phase 6 — billing tests

Add tests for invoice workflow.

Required tests:

1. draft invoice from appointment
2. draft invoice includes service line
3. repeated draft from same appointment returns existing invoice, does not duplicate
4. add invoice line while draft
5. update invoice line while draft
6. delete invoice line while draft
7. issue invoice generates final invoice number
8. cannot edit invoice lines after issue
9. record partial payment
10. record final payment
11. reject payment above total amount
12. mark paid requires billing.mark_paid
13. cannot cancel paid invoice in MVP workflow
14. invoice total and payment_status are recalculated correctly

Acceptance criteria:

- Billing state transitions are deterministic.
- PaymentTransaction is the source of payment history.

## Phase 7 — audit tests

Add tests for audit consistency.

Required tests:

1. patient update includes before_json and after_json
2. appointment update includes before_json and after_json
3. inventory batch create is audited
4. stock write-off is audited with reason
5. purchase order receive audits batch and movement creation
6. invoice payment is audited
7. API key actor appears as api_key, not user/system
8. audit log requires audit.read permission

Acceptance criteria:

- Every critical mutation can be reconstructed from audit log.

## Phase 8 — transaction rollback tests

Add explicit rollback tests.

Required tests:

1. appointment complete-with-consumption fails if stock insufficient and appointment remains not completed
2. purchase order receive with two valid lines and one invalid line creates no batches and no movements
3. invoice payment above total creates no payment and does not change invoice status
4. stock transfer failure leaves source batch unchanged

Acceptance criteria:

- Multi-step domain operations are atomic.

## Phase 9 — CI baseline

Add GitHub Actions workflow.

File:

`.github/workflows/ci.yml`

Workflow should run on push and pull_request.

Jobs:

Backend:

- checkout
- setup Python
- install backend dependencies
- run lint if configured
- run pytest

Frontend:

- setup Node
- install frontend dependencies
- run TypeScript check if configured
- run frontend build

Optional integration job:

- start PostgreSQL service
- run Alembic migrations
- run backend tests against PostgreSQL

Acceptance criteria:

- CI fails if tests fail.
- CI fails if frontend does not build.
- README documents CI status and local test command.

## Phase 10 — OpenAPI and response models

Stabilize API contracts.

Tasks:

- Add response_model to remaining major routes.
- Avoid returning raw SQLAlchemy objects where sensitive fields may leak.
- Add ErrorResponse schema.
- Add examples to important request schemas.
- Ensure API key raw value is returned only at creation.
- Ensure password_hash and key_hash never appear in responses.

Priority endpoints:

- auth login
- auth API key creation/listing
- patients
- appointments
- schedule/day
- ai/free-slots
- inventory
- purchase-orders
- invoices
- audit-log

Acceptance criteria:

- `/docs` is usable as an integration contract for AI agents and external systems.

## Phase 11 — fiscalization adapter stub

Do not implement Croatian fiscalization fully yet. Add architectural boundary.

Add module:

`backend/app/services/fiscalization.py`

Classes/interfaces:

- `FiscalizationResult`
- `FiscalizationProvider`
- `NoopFiscalizationProvider`
- `CroatiaFiscalizationProviderStub`

Behavior:

- Issued invoice can optionally call provider.
- Noop provider returns status `not_configured`.
- Stub should not call real external services.
- Store fiscalization_status and fiscalization_reference if fields exist.
- Audit fiscalization attempts.

Acceptance criteria:

- Future Croatian fiscalization can be added without rewriting invoice logic.
- Current local development remains safe and offline.

## Phase 12 — production hardening basics

Add basic security hardening.

Tasks:

- Document required production env vars.
- Enforce warning/error if JWT_SECRET is default in production mode.
- Add token expiration configuration.
- Add simple login rate limiting or document TODO if too large.
- Add CORS per environment.
- Add backup script:
  - `scripts/backup_postgres.sh`
- Add restore instructions.
- Add `SECURITY.md`.
- Add `docs/DEPLOYMENT_GOOGLE_CLOUD.md` with Cloud Run + Cloud SQL direction.

Acceptance criteria:

- Project clearly distinguishes local/dev from production.
- No one can accidentally deploy with `change-this-local-secret` in production.

## Phase 13 — frontend operational flows after backend tests pass

Only after tests and CI are green.

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

- A clinic user can perform daily workflows without curl.
- Dangerous actions ask for confirmation.
- Form validation mirrors backend validation.

## Phase 14 — modular workflow engine foundation

Only after hardening.

Add manifest structure:

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

Initial modules:

- gastroenterology
- endoscopy
- dermatology_aesthetics
- colonoscopy_prep
- h_pylori
- sibo_imo
- mounjaro

Start simple:

- load services
- load material templates
- expose modules via API
- no dynamic code execution

Acceptance criteria:

- Adding a new module does not require editing core models.
- Module manifests are data/config, not arbitrary executable plugins.

## Coding rules

- Keep commits small and coherent.
- Add tests with every important business rule.
- Do not weaken permission checks.
- Do not allow AI API keys to do destructive operations by default.
- Use transactions for multi-step domain operations.
- Do not return secrets.
- Do not add real external fiscalization calls yet.
- Prefer PostgreSQL-compatible tests for locking/transactions.
- Keep UI labels in Croatian when user-facing.
- Keep code/API names in English.

## Suggested commit sequence

1. `test: add backend pytest infrastructure`
2. `test: cover appointment conflict and scheduling rules`
3. `test: cover rbac and ai api key permissions`
4. `test: cover inventory ledger and fefo behavior`
5. `test: cover purchase order receiving workflow`
6. `test: cover billing invoice and payment workflow`
7. `test: cover structured audit logging`
8. `ci: add backend and frontend github actions workflow`
9. `docs: stabilize openapi response schemas and examples`
10. `feat: add fiscalization provider stub`
11. `chore: add production hardening docs and backup scripts`
12. `feat: add frontend operational workflows for stock receiving and billing`
13. `feat: add module manifest loader foundation`

## Definition of done for this sprint

This sprint is done when:

- backend tests exist and pass
- CI runs on push and PR
- appointment/inventory/procurement/billing critical workflows are covered
- AI API key boundaries are tested
- audit before/after is tested
- transaction rollback is tested
- OpenAPI schemas are safer and clearer
- fiscalization has a stub boundary
- README documents testing, CI and production warnings

Do not proceed to broad new feature work until this is complete.
