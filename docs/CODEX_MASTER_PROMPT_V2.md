# Codex master prompt v2 — ASTRA Clinic Core hardening sprint

Use this prompt in Codex for the next development sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack software architect and developer.

You are continuing work on `radicdavor/ASTRA-Clinic-Core`, an open-source modular, API-first clinic operations platform.

The current repository already has:

- FastAPI backend
- PostgreSQL
- Alembic documented in README
- React + TypeScript + Vite frontend
- Docker Compose deployment
- JWT authentication
- permission-based RBAC in core routes
- structured audit model
- request-id middleware
- appointment conflict validation
- AI API key scopes
- inventory models
- stock batches and FEFO consumption
- suppliers
- purchase orders
- invoices
- service material templates

Your task is not to rewrite the project. Your task is to harden the next layer: **inventory, procurement, billing, tests and API correctness**.

## Strategic direction

ASTRA Clinic Core should remain a clinic operating system, not a full EMR and not a bloated ERP.

It should answer operational questions:

- Who is scheduled today?
- What service is planned?
- Which room and provider are needed?
- Which materials will be consumed?
- What needs to be ordered?
- What should be billed?
- Which actor made which change?
- Can an AI agent safely create or read this data?

## Non-negotiable rule

Do not add new flashy features until these are correct:

1. permission enforcement
2. audit consistency
3. inventory ledger correctness
4. purchase receiving workflow
5. billing workflow foundation
6. tests

## Phase 1 — migrate inventory/procurement/billing routes to permission actor model

Current issue:

Core routes use `require_permission`, but inventory/procurement/billing routes still use `get_current_user` in many places.

Refactor all routes in `backend/app/api/routes/inventory.py` to use Actor + permission dependencies.

Permissions to enforce:

Inventory:

- `inventory.read` for list/read endpoints
- `inventory.write` for create/update item and batch entry
- `inventory.adjust` for stock adjustments
- `inventory.write_off` for write-off
- `inventory.transfer` for stock transfer if permission exists; otherwise add it

Suppliers:

- `procurement.read` for supplier read/list
- `procurement.write` for supplier create/update

Purchase orders:

- `procurement.read` for read/list
- `procurement.write` for create/update/receive

Invoices:

- `billing.read` for read/list
- `billing.write` for create/update
- `billing.mark_paid` for marking paid

Service material templates:

- `services.read` or `inventory.read` for reading templates
- `services.write` or `inventory.write` for creating/updating/deleting templates

Acceptance criteria:

- No inventory/procurement/billing endpoint uses raw `get_current_user` unless there is a strong reason.
- API key / AI agent cannot write off stock, adjust stock or mark invoices paid without explicit scope.
- All routes receive `Actor`, not only `User`.

## Phase 2 — make audit consistent across inventory/procurement/billing

Current issue:

Core routes use before/after snapshots. Inventory/procurement/billing routes still audit mostly summary-only.

Tasks:

- Use the same audit helper style as core routes.
- Include `before_json` and `after_json` for:
  - InventoryItem create/update
  - InventoryBatch create
  - StockMovement create
  - Supplier create/update
  - PurchaseOrder create/update/receive
  - Invoice create/update/mark-paid
  - ServiceMaterialTemplate create/update/delete
- Include actor_type and actor_api_key_id.
- Include request_id via Request.

Acceptance criteria:

- Every create/update/delete or financial/stock state transition has structured audit.
- AI API key actions are audit logged as API-key actor, not as anonymous/system.

## Phase 3 — implement real purchase order lines and receiving

Current issue:

`/purchase-orders/{id}/receive` appears to set status to received. That is not sufficient.

Add schemas:

- PurchaseOrderLineCreate
- PurchaseOrderLineUpdate
- PurchaseOrderReceiveLine
- PurchaseOrderReceiveRequest
- PurchaseOrderOut with lines

Add endpoints:

- `GET /api/purchase-orders/{order_id}/lines`
- `POST /api/purchase-orders/{order_id}/lines`
- `PATCH /api/purchase-orders/{order_id}/lines/{line_id}`
- `DELETE /api/purchase-orders/{order_id}/lines/{line_id}`
- `POST /api/purchase-orders/{order_id}/receive`

Receiving request example:

```json
{
  "lines": [
    {
      "purchase_order_line_id": 1,
      "quantity_received": 5,
      "lot_number": "LOT-2026-001",
      "expiration_date": "2027-07-01",
      "location_id": 1,
      "purchase_price": 12.50
    }
  ]
}
```

Receiving behavior:

- Validate purchase order exists.
- Validate line belongs to order.
- Validate quantity_received > 0.
- Validate cumulative received quantity does not exceed ordered quantity unless admin override is explicitly implemented.
- Create InventoryBatch for each received line.
- Create StockMovement with movement_type `purchase_receipt`.
- Update PurchaseOrderLine.quantity_received.
- Recalculate InventoryItem.current_stock.
- Update PurchaseOrder.status:
  - `ordered` or `draft` remains if nothing received
  - `partially_received` if some but not all lines received
  - `received` if all quantities received
- Audit before/after.

Acceptance criteria:

- Partial receive works.
- Receiving material immediately updates stock.
- Receiving requires LOT/expiration when the item has tracking enabled.
- PO status is derived from lines, not manually guessed.

## Phase 4 — strengthen inventory ledger rules

Current issue:

Inventory logic is better, but still needs stronger rules and tests.

Tasks:

- Treat InventoryBatch quantities as source of truth.
- Treat InventoryItem.current_stock as derived cache.
- Add a service function to recalculate one item and all items.
- Add admin endpoint or management command:
  - `POST /api/inventory/recalculate-stock`
- Add DB-level check constraints where practical:
  - batch quantity >= 0
  - movement quantity > 0
  - item current_stock >= 0
- Ensure stock movement does not mutate inventory incorrectly when movement_type is inappropriate.
- Separate manual stock movement from domain-specific functions where possible.
- Add optional merge-on-transfer behavior:
  - if target location already has same item + lot + expiration_date + supplier + purchase_price, increase existing batch
  - otherwise create new batch

Acceptance criteria:

- Stock never becomes negative.
- Transfer preserves total item stock.
- FEFO preserves total stock except consumed quantity.
- Recalculate endpoint repairs current_stock if cache gets out of sync.

## Phase 5 — appointment material consumption workflow

Improve the existing appointment material consumption endpoints.

Endpoints should exist and be correct:

- `GET /api/appointments/{id}/suggest-material-consumption`
- `POST /api/appointments/{id}/consume-materials`
- `POST /api/appointments/{id}/complete-with-consumption`

Behavior:

- Suggest based on `ServiceMaterialTemplate`.
- Include item name, SKU, default quantity, required, variable_quantity_allowed, available stock and warnings.
- Allow user override.
- For variable quantity items like propofol, do not auto-consume unless provided or configured.
- Use FEFO.
- If insufficient stock, fail the transaction unless user has override permission to complete without consumption.
- Completing appointment should be atomic with consumption.

Acceptance criteria:

- Completion either consumes all valid materials and marks appointment completed, or rolls back.
- User can edit suggested consumption.
- Required materials with insufficient stock generate clear error.

## Phase 6 — billing workflow foundation

Current issue:

Invoices exist, but billing is too shallow.

Add or improve:

Models:

- PaymentTransaction
- optional InvoiceNumberSequence or service function for invoice number generation

Invoice statuses:

- draft
- issued
- cancelled
- paid
- partially_paid
- refunded

Payment statuses can remain separate, but should be derived if possible.

Endpoints:

- `POST /api/appointments/{id}/draft-invoice`
- `GET /api/invoices/{invoice_id}/lines`
- `POST /api/invoices/{invoice_id}/lines`
- `PATCH /api/invoices/{invoice_id}/lines/{line_id}`
- `DELETE /api/invoices/{invoice_id}/lines/{line_id}`
- `POST /api/invoices/{invoice_id}/payments`
- `GET /api/invoices/{invoice_id}/payments`

Draft invoice from appointment:

- Use Appointment.service.price.
- Add one InvoiceLine for service.
- Optionally include billable inventory items later, but do not overcomplicate now.

Payment transaction:

- amount
- method
- reference
- paid_at
- created_by

Croatian fiscalization preparation:

Do not implement fiscalization yet. Add adapter interface only:

- `FiscalizationProvider`
- `NoopFiscalizationProvider`

Add optional invoice fields:

- operator
- business_unit
- register_id
- vat_id/oib where appropriate
- fiscalization_status
- fiscalization_reference

Acceptance criteria:

- Invoice can be generated from appointment.
- Invoice can have lines.
- Payments are separate records.
- Marking paid is permission protected.

## Phase 7 — response models and OpenAPI quality

Current issue:

Many routes return ORM objects directly. For AI agents and external integration, OpenAPI must be precise.

Tasks:

- Add output Pydantic schemas.
- Add `response_model` for main endpoints.
- Hide internal fields.
- Add examples to important request schemas.
- Ensure API docs are clear for AI agents.

Priority response models:

- PatientOut
- AppointmentOut
- ServiceOut
- InventoryItemOut
- InventoryBatchOut
- StockMovementOut
- SupplierOut
- PurchaseOrderOut
- PurchaseOrderLineOut
- InvoiceOut
- InvoiceLineOut
- AuditLogOut

Acceptance criteria:

- `/docs` shows predictable schemas.
- No password hash, API key hash or secret is ever returned.

## Phase 8 — tests

Add test coverage before adding new modules.

Use pytest for backend.

Required tests:

Auth/RBAC:

- login success
- permission denial
- AI API key allowed scope
- AI API key denied forbidden endpoint

Appointments:

- create appointment
- reject end_time <= start_time
- reject provider overlap
- reject room overlap
- allow cancelled appointment not to block slot

Inventory:

- create item
- create batch
- FEFO consumes earliest expiration first
- insufficient stock rolls back
- transfer preserves total stock
- write-off requires reason
- adjustment requires reason
- recalculate stock repairs cache

Procurement:

- create PO
- add PO line
- partial receive
- full receive
- reject over-receive
- receive creates batch and stock movement

Billing:

- draft invoice from appointment
- add invoice line
- record payment
- permission denial for mark-paid

Audit:

- appointment update has before/after
- stock write-off has before/after and reason
- API key action is recorded as api_key actor

Acceptance criteria:

- tests run with one command.
- all critical business rules have coverage.

## Phase 9 — frontend operational screens

After backend correctness, add UI screens.

Required screens:

Inventory:

- Item detail
- Create/edit item
- Batch list/detail
- Receive stock
- Transfer stock
- Write off stock
- Adjustment
- Recalculate stock admin action

Procurement:

- Purchase order detail
- Add/edit lines
- Receive order partially
- Show ordered/received/remaining

Appointments:

- Complete appointment with material consumption
- Material suggestion preview
- Conflict error display

Billing:

- Draft invoice from appointment
- Invoice detail with lines
- Add payment

Audit:

- Filters by entity, action, actor_type, date

Acceptance criteria:

- A clinic user can perform daily operational tasks without curl.
- Dangerous actions require confirmation and reason.

## Phase 10 — modular medical workflows

Only after hardening the above, start true modular workflows.

Add a module manifest format:

`modules/<module_key>/module.json`

Example:

```json
{
  "key": "gastroenterology",
  "name": "Gastroenterologija",
  "version": "0.1.0",
  "services": "services.json",
  "material_templates": "material_templates.json",
  "workflows": "workflows.json",
  "patient_instructions": "patient_instructions.json",
  "ai_prompts": "ai_prompts.json"
}
```

Initial modules:

- gastroenterology
- endoscopy
- dermatology_aesthetics
- h_pylori
- colonoscopy_prep
- sibo_imo
- mounjaro

Do not overbuild. Start with service definitions and material templates.

## Coding rules

- Keep commits small and coherent.
- Do not break existing Docker startup.
- Do not return raw SQLAlchemy models where sensitive fields may leak.
- Do not store raw API keys.
- Do not allow AI API key to perform destructive operations by default.
- Use transactions for inventory and billing operations.
- Add tests for every business rule.
- Prefer clear Croatian UI labels in frontend.
- Keep English code names and API names.

## Suggested commit sequence

1. `refactor: secure inventory routes with permission actors`
2. `feat: add structured audit to inventory procurement billing`
3. `feat: implement purchase order lines and receiving workflow`
4. `feat: strengthen inventory ledger and stock recalculation`
5. `feat: complete appointment material consumption workflow`
6. `feat: add invoice lines and payment transactions`
7. `docs: improve OpenAPI schemas and examples`
8. `test: add backend coverage for scheduling inventory procurement billing`
9. `feat: add frontend operational inventory screens`
10. `feat: add modular medical workflow manifests`

## Definition of done for this sprint

The sprint is done when:

- inventory/procurement/billing use permission actors
- audit is structured across all critical routes
- purchase receiving actually creates stock
- inventory cannot go negative
- appointment completion can consume materials atomically
- invoice can be drafted from appointment
- AI API keys cannot access forbidden operations
- tests cover the critical business rules
- README is updated with new workflows
