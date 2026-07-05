# Codex master prompt v4 — test-driven hardening

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

## Context

ASTRA Clinic Core already has a serious MVP foundation:

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
- purchase orders with lines and receiving
- invoices with lines and payment transactions
- draft invoice from appointment
- invoice issuing with `InvoiceNumberSequence`
- service layer for billing and procurement

Do not add new modules in this sprint. Stabilize what exists.

## Sprint goal

Make the project test-driven, transaction-safe and CI-protected before adding new features.

Do not implement Google Calendar, fiscalization, voice agents, new medical modules, OpenEMR integration or major UI redesign in this sprint.

## Phase 1 — pytest infrastructure

Create backend test infrastructure:

```text
backend/tests/
  conftest.py
  factories.py
  test_auth_permissions.py
  test_appointments.py
  test_inventory.py
  test_procurement.py
  test_billing.py
  test_audit.py
```

Requirements:

- isolated test database
- deterministic factories
- one command to run tests
- tests must not mutate dev database

## Phase 2 — permission and API key tests

Add tests proving:

- admin can access critical endpoints
- user without `inventory.write_off` cannot write off stock
- user without `inventory.adjust` cannot adjust stock
- user without `billing.mark_paid` cannot create payment
- AI API key cannot perform forbidden stock or billing operations
- API key actions are audit logged as API-key actor

## Phase 3 — appointment tests

Test:

- create appointment
- reject `end_time <= start_time`
- reject provider overlap
- reject room overlap
- cancelled appointment does not block time
- update appointment revalidates conflicts
- audit contains before/after after update

## Phase 4 — inventory ledger tests

Test:

- create item and batch
- batch quantity cannot be negative
- stock movement quantity must be positive
- LOT tracking requires LOT number
- expiration tracking requires expiration date
- FEFO consumes earliest expiration first
- insufficient stock raises 409 and rolls back
- transfer preserves total stock
- write-off requires reason
- adjustment requires reason
- recalculate stock repairs corrupted `current_stock`
- `current_stock == sum(batch.quantity)` after operations

## Phase 5 — procurement tests

Test:

- create supplier
- create purchase order
- add/update/delete purchase order line
- delete unreceived line recalculates total
- cannot delete received line
- partial receive creates InventoryBatch and StockMovement
- full receive sets status to `received`
- over-receive is rejected
- tracking flags require LOT/expiration
- failed receive rolls back created batches and movements

## Phase 6 — billing tests

Test:

- draft invoice from appointment creates `DRAFT-...` invoice
- draft invoice creates one service line
- second draft request returns existing invoice
- issue invoice assigns official `ASTRA-YYYYMMDD-NNNNN` number
- only draft invoice can be issued
- issue requires at least one line
- issued invoice lines cannot be added, updated or deleted
- partial payment sets `partially_paid`
- full payment sets `paid`
- overpayment is rejected
- cancelled invoice cannot receive payment
- payment to draft invoice should be rejected
- mark-paid does not duplicate payment
- invoice number sequence does not generate duplicates

## Phase 7 — invoice status policy

Implement explicit invoice status transitions.

Recommended MVP transitions:

- draft -> issued
- draft -> cancelled
- issued -> partially_paid
- issued -> paid
- partially_paid -> paid
- issued -> cancelled only if no payments exist
- cancelled is terminal
- paid is terminal until refund/storno workflow exists

Rules:

- payment only on issued or partially_paid invoices
- draft invoices cannot receive payment
- cancelled invoices cannot receive payment
- issued/paid/cancelled invoice lines cannot be edited normally
- generic invoice PATCH must not override protected fields after issue

## Phase 8 — service-layer cleanup

Continue moving business logic out of routes.

Add if useful:

```text
backend/app/services/appointment_materials.py
backend/app/services/audit_helpers.py
```

Rules:

- no endpoint calls another endpoint
- service functions do not commit internally
- endpoint owns commit/rollback boundary
- service functions are unit-testable

## Phase 9 — rollback tests

Add explicit rollback tests:

- appointment completion with two required materials, second insufficient: no stock consumed and appointment not completed
- purchase receive with two lines, second invalid: no batch or movement remains from first line
- payment failure does not alter invoice status
- invoice issue failure behavior is documented and tested

## Phase 10 — CI

Add GitHub Actions:

```text
.github/workflows/ci.yml
```

Run on push and pull request:

- backend install
- migrations against test PostgreSQL
- pytest
- frontend install
- TypeScript/frontend build

## Phase 11 — docs and security

Add or update:

```text
SECURITY.md
docs/TESTING.md
docs/SECURITY_MODEL.md
docs/INVENTORY_LEDGER.md
docs/PROCUREMENT_WORKFLOW.md
docs/BILLING_WORKFLOW.md
docs/TRANSACTION_BOUNDARIES.md
```

README must state:

- default credentials are development-only
- change admin password immediately
- set strong JWT secret
- restrict CORS in production
- use HTTPS
- configure backups
- system is not a certified EMR
- system is not a certified medical device
- real patient data requires GDPR-compliant deployment and access control review

## Phase 12 — license decision

Add a `LICENSE` or `docs/LICENSE_DECISION.md`.

Recommended direction:

- AGPL-3.0 if the project should remain open-source even as a hosted/SaaS derivative
- Apache-2.0 if maximum adoption and commercial flexibility matter more

## Suggested commit sequence

1. `test: add pytest infrastructure and fixtures`
2. `test: cover permissions and ai api key scopes`
3. `test: cover appointment conflicts and audit snapshots`
4. `test: cover inventory fefo transfer and rollback`
5. `test: cover procurement receiving workflow`
6. `test: cover billing issue payment and invoice status rules`
7. `feat: enforce invoice status transition policy`
8. `refactor: extract appointment material consumption service`
9. `ci: add backend tests and frontend build workflow`
10. `docs: add security testing ledger billing and transaction docs`
11. `docs: add license decision`

## Definition of done

This sprint is complete when:

- pytest suite exists
- CI exists
- permission tests pass
- appointment conflict tests pass
- inventory ledger tests pass
- procurement tests pass
- billing tests pass
- rollback tests pass
- invoice status transitions are explicit
- README and SECURITY.md clearly warn about production use
