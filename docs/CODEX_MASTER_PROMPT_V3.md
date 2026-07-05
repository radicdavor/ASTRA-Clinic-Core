# Codex master prompt v3 — testing, transactions and production discipline

Use this prompt in Codex for the next development sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack software architect and developer.

You are working on `radicdavor/ASTRA-Clinic-Core`, an open-source modular clinic operations platform.

The project already has a meaningful MVP foundation:

- FastAPI backend
- PostgreSQL
- Alembic workflow documented
- React + TypeScript frontend
- Docker Compose
- JWT auth
- permission-based RBAC
- scoped API keys for AI agents
- structured audit log
- appointment conflict validation
- inventory items, batches and stock movements
- FEFO consumption
- suppliers
- purchase orders with lines
- purchase receiving that creates inventory batches
- invoices with invoice lines
- payment transactions
- draft invoice from appointment
- appointment material consumption workflow

Your task in this sprint is not to add new modules. Your task is to prove correctness and reduce risk.

## Sprint theme

**Stabilize before expanding.**

Do not add Google Calendar, new medical modules, voice agents, fiscalization implementation or major UI redesign in this sprint.

Focus on:

1. tests
2. service-layer refactor
3. atomic transactions
4. invoice numbering correctness
5. CI
6. security/compliance documentation

## Phase 1 — add backend test infrastructure

Add pytest-based backend tests.

Recommended tools:

- pytest
- pytest-asyncio only if needed
- httpx TestClient or FastAPI TestClient
- a dedicated test database
- SQLAlchemy transaction rollback fixture

Create structure:

```text
backend/tests/
  conftest.py
  test_auth_permissions.py
  test_appointments.py
  test_inventory.py
  test_procurement.py
  test_billing.py
  test_audit.py
```

Add command:

```bash
make test
```

or document:

```bash
cd backend && pytest
```

Acceptance criteria:

- tests can be run locally with one command
- test database is isolated from development database
- tests do not depend on manual seed unless the fixture explicitly seeds data

## Phase 2 — critical permission tests

Test that RBAC and AI API keys actually work.

Required tests:

1. admin can access all critical endpoints
2. user without `inventory.write_off` cannot call `/api/inventory/write-off`
3. user without `billing.mark_paid` cannot create payment
4. API key with only `ai.appointments.create` cannot mark invoice paid
5. API key with only AI scopes cannot adjust stock
6. API key action is audit logged as `api_key`

Acceptance criteria:

- destructive operations fail with 403 without explicit permission
- API key scopes are enforced

## Phase 3 — appointment tests

Required tests:

1. create appointment succeeds
2. reject appointment if `end_time <= start_time`
3. reject provider overlap
4. reject room overlap
5. cancelled appointment does not block slot
6. no_show appointment does not block slot if configured as non-blocking
7. update appointment revalidates conflicts
8. audit log contains before/after after update

Acceptance criteria:

- double booking cannot pass tests
- appointment conflict behavior is documented and stable

## Phase 4 — inventory ledger tests

Required tests:

1. create inventory item
2. create batch requires positive quantity
3. item with lot tracking requires lot number
4. item with expiration tracking requires expiration date
5. FEFO consumes earliest expiration batch first
6. insufficient stock raises 409 and does not change any batch
7. transfer preserves total stock
8. write-off requires reason
9. adjustment requires reason
10. recalculate stock repairs `current_stock`
11. `current_stock` equals sum of all batch quantities after operations

Acceptance criteria:

- all stock-changing paths are covered
- negative stock cannot occur
- rollback behavior is verified

## Phase 5 — procurement tests

Required tests:

1. create supplier
2. create purchase order
3. add purchase order line
4. update purchase order line recalculates total
5. delete unreceived purchase order line recalculates total
6. cannot delete received purchase order line
7. partial receive creates InventoryBatch and StockMovement
8. full receive changes PO status to `received`
9. over-receive is rejected
10. tracked item requires LOT/expiration on receiving
11. receiving recalculates inventory stock

Acceptance criteria:

- purchase receiving is proven to be real stock receiving
- PO status is derived from line quantities

## Phase 6 — billing tests

Required tests:

1. draft invoice from appointment creates invoice and service line
2. second draft request for same appointment returns existing invoice
3. add invoice line recalculates total
4. update invoice line recalculates total
5. delete invoice line recalculates total
6. create partial payment sets status to `partially_paid`
7. create full payment sets status to `paid`
8. mark-paid creates remaining payment only once
9. overpayment behavior is defined and tested: either reject or allow with explicit status
10. user without `billing.mark_paid` cannot pay invoice

Acceptance criteria:

- invoice total and payment status are correct
- payment logic cannot double count relationship objects

## Phase 7 — refactor endpoint logic into service layer

Current risk:

Some endpoint functions call other endpoint functions or contain too much business logic.

Refactor into services:

```text
backend/app/services/
  appointments.py
  inventory.py
  procurement.py
  billing.py
  audit.py
```

Required service functions:

Appointments:

- `validate_appointment_payload(...)`
- `complete_appointment_with_consumption(...)`

Inventory:

- `consume_fefo(...)`
- `transfer_batch(...)`
- `recalculate_stock(...)`
- `recalculate_all_stock(...)`

Procurement:

- `recalculate_purchase_order_total(order)`
- `derive_purchase_order_status(order)`
- `receive_purchase_order(order, payload, actor, request)`

Billing:

- `next_invoice_number(...)`
- `draft_invoice_from_appointment(...)`
- `recalculate_invoice_total(invoice)`
- `record_payment(invoice, payment_payload, actor)`
- `mark_invoice_paid(invoice, method, actor)`

Important:

- Do not call endpoint functions from endpoint functions.
- Endpoint functions should validate request/auth, call service, commit/return.
- Keep transaction boundaries explicit.

Acceptance criteria:

- `mark_paid` no longer calls `create_payment` endpoint function.
- purchase receiving logic lives in service layer or is cleanly isolated.
- tests still pass.

## Phase 8 — atomic transaction behavior

Test and enforce atomicity.

Critical scenario:

Appointment completion consumes multiple materials. If material 1 is available but material 2 is not, no material should be consumed and appointment should not be completed.

Tasks:

- ensure service functions do not commit internally
- endpoint commits only after all operations succeed
- tests verify rollback on failure

Required rollback tests:

1. material consumption failure rolls back all batch changes
2. PO receiving failure rolls back all received lines and batch creation
3. invoice payment failure does not partially update invoice status

Acceptance criteria:

- no partial business state after failure

## Phase 9 — invoice number safety

Current risk:

Generating invoice number from last ID is not concurrency safe.

Implement safer strategy.

Preferred design:

- draft invoice can exist without official invoice number OR with temporary internal draft number
- official invoice number is assigned only on `issue` action
- create `InvoiceNumberSequence` table or use a DB sequence

Add invoice issue endpoint:

```text
POST /api/invoices/{invoice_id}/issue
```

Rules:

- only draft invoice can be issued
- issued invoice gets official invoice_number
- invoice_number must be unique and concurrency safe
- issued invoice lines should not be freely editable without special correction/storno workflow

Acceptance criteria:

- test concurrent-ish issuing or sequence uniqueness
- no duplicate invoice numbers
- draft invoices do not consume official fiscal numbering if that is the chosen policy

## Phase 10 — invoice status transition rules

Define allowed transitions:

- draft -> issued
- draft -> cancelled
- issued -> partially_paid
- issued -> paid
- issued -> cancelled only if no payments and if policy allows
- paid -> refunded later, not necessarily implemented now
- cancelled is terminal

Rules:

- cannot add payment to cancelled invoice
- cannot edit issued invoice lines without explicit permission or correction flow
- cannot delete paid invoice

Acceptance criteria:

- invalid transitions return 409 or 422
- tests cover invalid transitions

## Phase 11 — improve material consumption semantics

Clarify service material template behavior.

Add explicit fields or derived behavior in suggestion response:

- `auto_consumable`
- `requires_user_quantity`
- `optional`
- `available_stock`
- `warning`

Rules:

- required + non-variable item can be auto-consumed
- required + variable item must have user-provided quantity before completion
- optional item is only consumed if user selects it
- if required item has insufficient stock, completion fails unless special override permission is later added

Acceptance criteria:

- propofol-like variable required material does not silently consume default quantity
- required variable material without user quantity blocks completion with clear message

## Phase 12 — CI pipeline

Add GitHub Actions.

Create:

```text
.github/workflows/ci.yml
```

Run:

- backend install
- backend lint if configured
- backend pytest
- frontend install
- frontend build
- optional Docker Compose smoke test

Acceptance criteria:

- pull requests and pushes run CI
- failing tests block confidence immediately

## Phase 13 — frontend smoke tests or build hardening

If full frontend test setup is too much, at minimum ensure:

- `npm run build` works in CI
- TypeScript build has no errors
- API client types are not obviously broken

Optional:

- add Vitest smoke tests for login/dashboard/inventory pages

Acceptance criteria:

- frontend build is part of CI

## Phase 14 — README security and compliance update

Update README with explicit warnings:

- default credentials are development-only
- change `JWT_SECRET` in any real deployment
- change admin password immediately
- configure production CORS
- use HTTPS
- back up PostgreSQL
- this is not a certified EMR
- this is not a certified medical device
- real patient data requires GDPR-compliant deployment, DPA/vendor assessment and access controls

Add `SECURITY.md`:

- supported versions
- vulnerability reporting
- secret handling
- PHI/PII warning

Add `LICENSE` decision placeholder if not decided.

Acceptance criteria:

- no one can confuse local demo config with production-safe deployment

## Phase 15 — architecture docs update

Update or add:

```text
docs/TESTING.md
docs/SECURITY_MODEL.md
docs/BILLING_WORKFLOW.md
docs/INVENTORY_LEDGER.md
```

Keep docs concise and operational.

## Strict rules for this sprint

- Do not add new medical modules.
- Do not implement Croatian fiscalization yet; only prepare workflow safely.
- Do not add voice agent functionality.
- Do not add Google Calendar integration.
- Do not perform large frontend redesign.
- Do not hide failing tests.
- Do not store raw API keys.
- Do not introduce endpoint-to-endpoint calls.
- Do not commit production secrets.

## Suggested commit sequence

1. `test: add backend pytest infrastructure`
2. `test: cover permissions api keys and appointment conflicts`
3. `test: cover inventory ledger fefo and rollback behavior`
4. `test: cover procurement receiving and billing payments`
5. `refactor: move procurement and billing logic into services`
6. `fix: make appointment material consumption atomic`
7. `feat: add safe invoice issuing and numbering workflow`
8. `feat: enforce invoice status transitions`
9. `ci: add backend and frontend continuous integration`
10. `docs: add security compliance testing and workflow documentation`

## Definition of done

This sprint is done when:

- backend critical tests pass
- CI runs tests and frontend build
- endpoint business logic is moved into service functions where appropriate
- appointment material consumption is atomic
- PO receiving rollback behavior is tested
- billing payment logic is tested
- invoice numbering is concurrency safer
- README and SECURITY.md warn clearly about production use

Only after this sprint should the project move to new modules, Google Calendar, fiscalization, advanced frontend or AI voice workflows.
