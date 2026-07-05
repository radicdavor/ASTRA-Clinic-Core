# Codex master prompt — ASTRA Clinic Core next phase

Use this prompt in Codex to continue development of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect and developer.

You are working on the open-source repository `radicdavor/ASTRA-Clinic-Core`.

The project is ASTRA Clinic Core: a modular, API-first clinic operations platform. It is not intended to become a bloated full EMR in the first phase. It should become a lightweight clinic operating system focused on:

- patients
- appointments
- daily schedule
- patient flow
- medical service catalog
- modular medical workflows
- AI-agent integration
- inventory and stock movements
- procurement and suppliers
- billing preparation
- auditability
- local-first deployment
- future Google Cloud deployment

Current stack:

- Backend: Python FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy 2.x
- Frontend: React + TypeScript + Vite
- Auth: JWT
- Deployment: Docker Compose

Your job is to transform the current MVP scaffold into a safer, more correct, production-oriented foundation.

Do not rewrite the project from scratch unless absolutely necessary. Improve it incrementally.

## Core philosophy

ASTRA Clinic Core must be:

1. API-first
2. modular
3. local-first
4. cloud-ready
5. auditable
6. secure by default
7. AI-agent ready, but not AI-agent reckless
8. inventory-aware from day one
9. prepared for Croatian billing/fiscalization integration later
10. simple enough to run in a private clinic

## Most important architectural rule

Do not build a giant EMR.

Build the operational layer of a clinic:

- who is coming today
- why they are coming
- what service they need
- which room/provider is needed
- what status they are in
- what material will be consumed
- what should be billed
- what must be audited
- which external system or AI agent created the change

## High-priority problems to fix first

### 1. Database migrations

Currently, if the project uses `Base.metadata.create_all()` at startup, replace that with Alembic migrations.

Tasks:

- Add Alembic.
- Create initial migration covering all current models.
- Remove production reliance on `create_all()`.
- Add migration command to Docker startup or README.
- Add seed command separately.

Acceptance criteria:

- A clean PostgreSQL database can be created through migrations.
- Existing seed data can be inserted idempotently.

### 2. Permission-based RBAC

Role names alone are not enough.

Add a permission system.

Models:

- Permission
- RolePermission association table

Initial permissions:

- patients.read
- patients.write
- appointments.read
- appointments.write
- appointments.cancel
- services.read
- services.write
- modules.read
- inventory.read
- inventory.write
- inventory.adjust
- inventory.write_off
- procurement.read
- procurement.write
- billing.read
- billing.write
- billing.mark_paid
- audit.read
- admin.manage_users
- ai.appointments.create
- ai.patients.create
- ai.free_slots.read

Initial roles:

- admin: all permissions
- physician: patients.read/write, appointments.read/write, services.read, inventory.read, billing.read
- nurse: patients.read, appointments.read/write, inventory.read, inventory.write limited if possible
- receptionist: patients.read/write, appointments.read/write, services.read, billing.read
- inventory_manager: inventory.read/write/adjust/write_off, procurement.read/write
- billing: billing.read/write/mark_paid, patients.read, appointments.read
- ai_agent: only ai.* permissions and explicitly allowed read endpoints

Acceptance criteria:

- Sensitive endpoints require explicit permissions.
- AI agent cannot access audit log, inventory adjustment, write-off or invoice payment unless explicitly granted.

### 3. Structured audit log

Upgrade audit logging.

AuditLog should include:

- id
- actor_type: user/api_key/ai_agent/system
- actor_user_id nullable
- actor_api_key_id nullable
- action
- entity_type
- entity_id
- before_json
- after_json
- summary
- request_id
- ip_address
- user_agent
- created_at

Add middleware to generate request_id.

All create/update/delete operations must audit before and after state.

Acceptance criteria:

- Updating an appointment records the exact old and new values.
- Deleting an appointment records the deleted state.
- Audit log can be filtered by date, actor, action and entity.

### 4. Appointment conflict validation

Appointment scheduling must be safe.

Rules:

- end_time must be greater than start_time
- duration_minutes must match or be calculated from start/end
- status must be enum, not arbitrary string
- source must be enum, not arbitrary string
- prevent overlapping appointments for the same provider
- prevent overlapping appointments for the same room
- cancelled/no_show appointments should not block time unless configured
- admin override may exist but must be audited

Add endpoint:

- `GET /api/ai/free-slots`

Input examples:

- provider_id optional
- service_id required or duration_minutes required
- date_from
- date_to
- room_id optional

Acceptance criteria:

- A provider cannot be double-booked.
- A room cannot be double-booked.
- AI agent can search free slots before creating appointments.

### 5. Inventory ledger correctness

Inventory is not just a table. It is a ledger.

Rules:

- InventoryBatch.quantity is the operational quantity by batch/location.
- InventoryItem.current_stock is only a cached aggregate.
- Stock movements are the audit trail.
- No batch quantity may become negative.
- No item may be consumed if not enough stock exists.
- Movement types must be enum values.
- Adjustment and write-off require a reason.
- Transfer must be atomic and must preserve quantity.

Movement types:

- purchase_receipt
- consumption
- transfer_out
- transfer_in
- adjustment
- write_off
- return_to_supplier

FEFO consumption:

- consume first from batches with earliest expiration date
- null expiration dates come last
- if insufficient stock, abort entire transaction

Acceptance criteria:

- FEFO consumption works across multiple batches.
- Stock cannot go below zero.
- Stock item current_stock equals the sum of all batch quantities.
- Every movement is audit logged.

### 6. Procurement workflow

Current purchase orders must be upgraded from simple headers to real procurement.

Add or complete:

- PurchaseOrderLine CRUD
- partial receiving
- receiving creates inventory batches
- receiving creates purchase_receipt stock movement
- PO statuses:
  - draft
  - ordered
  - partially_received
  - received
  - cancelled

Receiving payload should include:

- purchase_order_line_id
- quantity_received
- lot_number
- expiration_date
- location_id
- purchase_price

Acceptance criteria:

- One purchase order can contain multiple lines.
- Receiving can be partial.
- Received goods immediately appear in inventory.

### 7. Service material templates and appointment consumption

Each medical service can define default material consumption.

Examples:

Colonoscopy with sedation:

- IV cannula: 1 required
- examination gloves: 2 required
- propofol: variable
- biopsy forceps: optional
- polypectomy snare: optional

HarmonyCa treatment:

- HarmonyCa: 1 required
- cannula: 1 required
- needle: 1 required
- examination gloves: 2 required

Endpoints:

- `GET /api/appointments/{id}/suggest-material-consumption`
- `POST /api/appointments/{id}/consume-materials`
- `POST /api/appointments/{id}/complete-with-consumption`

Behavior:

- Suggest materials based on service material template.
- Allow user to accept, edit or remove suggested consumption.
- Consume material using FEFO.
- Mark appointment completed only if consumption succeeds or user explicitly completes without consumption if permitted.
- Audit everything.

Acceptance criteria:

- Completing an appointment can deduct materials from stock.
- User can modify the proposed quantities.
- Variable items such as propofol do not force a fixed quantity.

### 8. Billing preparation

Do not build full Croatian fiscalization yet. Prepare the architecture.

Improve invoice model:

- invoice number generator
- invoice status enum:
  - draft
  - issued
  - cancelled
  - paid
  - partially_paid
  - refunded
- payment transactions
- invoice lines CRUD
- create draft invoice from appointment
- Croatian-ready optional fields:
  - operator
  - business_unit
  - register_id
  - oib/vat_id
  - fiscalization_status
  - fiscalization_reference

Add adapter interface:

- `FiscalizationProvider`
- default implementation: `NoopFiscalizationProvider`

Acceptance criteria:

- Invoice can be generated from appointment and service price.
- Payment is a separate transaction.
- Future fiscalization can be plugged in without rewriting invoice logic.

### 9. API key authentication for AI agents

Do not let AI agents behave like normal users.

ApiKey should include:

- name
- key_hash
- scopes
- active
- expires_at
- last_used_at
- created_at

Add dependency:

- `get_current_actor`

Actor can be:

- human user via JWT
- api key / AI agent via header

Suggested header:

- `X-ASTRA-API-Key`

AI endpoint rules:

- AI can create patient only with scope `ai.patients.create`
- AI can create appointment only with scope `ai.appointments.create`
- AI can read free slots only with scope `ai.free_slots.read`
- AI cannot delete patients or appointments by default
- AI cannot mark invoice paid
- AI cannot perform stock adjustment or write-off

Acceptance criteria:

- API key is hashed at rest.
- Full key is shown only once at creation.
- AI calls are audit logged as actor_type `ai_agent` or `api_key`.

### 10. Frontend improvements

Add operational screens, not just lists.

Required frontend pages:

- appointment conflict feedback
- free slots view
- inventory item detail
- create/edit inventory item
- batch detail
- receive stock
- stock transfer
- write-off stock
- adjustment
- service material templates
- complete appointment with material consumption
- invoice detail
- create invoice from appointment
- audit log filters

UX principles:

- Croatian UI text is acceptable and preferred.
- Avoid clutter.
- Make the dashboard operational: what do I need to do today?
- Use clear status badges.
- Dangerous actions require confirmation.

### 11. Tests

Add tests before broad expansion.

Backend tests:

- auth login
- permission denial
- create patient
- create appointment
- appointment conflict rejection
- schedule/day
- FEFO consumption with two batches
- insufficient stock rollback
- low stock endpoint
- expiring endpoint
- purchase order partial receiving
- invoice draft from appointment
- audit before/after

Frontend tests:

- login smoke
- dashboard smoke
- inventory dashboard smoke

Acceptance criteria:

- Tests run with one command.
- CI can be added later easily.

## Implementation constraints

- Keep code clean and incremental.
- Prefer small commits.
- Do not remove existing working features unless replacing them with better equivalents.
- Use type hints in backend.
- Use Pydantic schemas for request and response models.
- Add response_model to important routes.
- Do not expose password hashes or internal secrets.
- Do not store raw API keys.
- Do not use SQLite as the main target now; PostgreSQL is the correct target.

## Suggested work order

Follow the commit plan in `docs/IMPLEMENTATION_COMMITS.md`.

Minimum next sequence:

1. Add Alembic migrations.
2. Add permission-based RBAC.
3. Upgrade audit log.
4. Add appointment conflict validation.
5. Correct inventory ledger rules.
6. Add purchase order lines and receiving workflow.
7. Add tests.

Stop after each coherent commit and summarize:

- files changed
- what was added
- how to test
- known limitations

## Final goal of this phase

At the end of this phase, the project should be a trustworthy technical foundation for:

- local clinic scheduling
- controlled AI-agent booking
- inventory management
- procurement
- material consumption per service
- billing preparation
- later Croatian fiscalization
- later Google Cloud deployment
