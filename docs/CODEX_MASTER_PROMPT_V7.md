# Codex master prompt v7 — Pilot Readiness Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect, product-minded developer and QA-focused maintainer.

ASTRA Clinic Core has implemented v6. The project now has:

- backend domain logic for appointments, inventory, procurement, billing and audit
- CI with backend tests and frontend typecheck/build
- PostgreSQL test fixture
- fiscalization boundary
- production safety checks
- release/QA/demo-data documentation
- Dashboard workflow for completing appointment with material consumption
- purchase order receiving UI
- invoice issue/payment UI
- API key management UI
- initial module manifest files

The project is now close to demo-ready.

The next sprint is:

**Pilot Readiness Sprint**

Main goal:

Prepare ASTRA Clinic Core for a closed internal demo/pilot using demo data only. Do not use real patient data.

Do not add broad new medical modules yet. First make one complete operational flow excellent.

## Pilot demo flow to optimize

The demo flow must cover:

1. Login as admin or physician.
2. Open daily dashboard.
3. See today’s appointments.
4. Complete an appointment with material consumption.
5. Verify stock was deducted and stock movement created.
6. Create draft invoice from appointment.
7. Issue invoice.
8. See fiscalization Noop/stub status.
9. Record payment.
10. Receive purchase order by line.
11. Verify inventory increased.
12. Review audit log for the above events.

This flow should be smooth enough for a live demo.

## Phase 1 — Add E2E or API-level demo smoke test

Add one full smoke test that proves the pilot flow.

Preferred options:

- Playwright E2E if feasible
- otherwise API-level smoke test with FastAPI TestClient/httpx

Required path:

- create or use seeded patient/provider/room/service
- create appointment
- create inventory item and batch
- attach service material template
- complete appointment with material consumption
- assert appointment completed
- assert stock reduced
- assert stock movement exists
- draft invoice from appointment
- issue invoice
- assert fiscalization fields exist
- record payment
- assert payment status paid or partially_paid
- create supplier/PO/line
- receive PO line
- assert stock increased
- assert audit records exist

Suggested file:

```text
backend/tests/integration/test_pilot_demo_flow.py
```

Acceptance criteria:

- One test proves the full demo flow.
- Test runs in CI.
- Test uses PostgreSQL if `TEST_DATABASE_URL` is available.

## Phase 2 — Appointment detail page

Current Dashboard has the operational workflow, but Appointments page is list-only.

Add appointment detail page.

Route:

```text
/appointments/:id
```

Appointment detail should show:

- patient name
- date/time
- service
- provider
- room
- status
- notes
- material consumption panel
- draft invoice / open invoice button
- related invoice if exists
- recent stock movements related to appointment if API supports it
- audit timeline if API supports it

From the appointment list and dashboard, clicking the appointment should open the detail page.

Acceptance criteria:

- A user can operate a single appointment from a dedicated screen.
- Dashboard remains fast, appointment detail handles deeper workflow.

## Phase 3 — Refine material consumption UI

Improve the Dashboard/Appointment detail material workflow.

Requirements:

- Clearly distinguish:
  - required fixed materials
  - required variable materials
  - optional materials
- Show available stock per item.
- Show warning if requested quantity exceeds stock.
- Disable confirm if required variable quantity is missing.
- Disable confirm if no required items can be consumed.
- Display backend errors clearly.
- After success, refresh appointment status and low-stock indicators.
- Make confirmation text explicit: “Ovo će skinuti materijal sa zalihe i završiti termin.”

Acceptance criteria:

- Clinician cannot easily make obvious material-entry mistakes.
- Backend remains source of truth.

## Phase 4 — Refine purchase order receiving UI

Improve purchase receiving.

Requirements:

- Show ordered, received and remaining quantities clearly.
- Default receive quantity to remaining.
- Block front-end over-receive before submit.
- Require LOT/expiration in UI when item tracking requires it.
- Show supplier name, order status and total amount.
- After receive, refresh inventory low-stock and order state.
- Show created/updated status: partially_received or received.
- Add confirmation dialog before receiving stock.

Acceptance criteria:

- Inventory manager can receive stock safely without curl.

## Phase 5 — Refine invoice issue/payment UI

Improve billing UI.

Requirements:

- From appointment detail, create/open invoice.
- Show invoice lines with totals.
- Allow editing only while draft.
- Disable issue if no lines or total <= 0.
- Confirmation before issuing invoice.
- Show fiscalization provider/status/message clearly.
- If provider is noop/stub, show visible warning: “Nije stvarna fiskalizacija.”
- Payment form should show remaining amount.
- Default payment amount to remaining.
- Prevent frontend overpayment before submit.
- Refresh payment status after payment.

Acceptance criteria:

- Reception/billing user can issue invoice and record payment safely.

## Phase 6 — API key scope UX hardening

Improve API key management UI.

Requirements:

- Group scopes into categories:
  - AI safe scopes
  - read-only scopes
  - operational write scopes
  - dangerous scopes
- Dangerous scopes should require extra confirmation.
- Never show key_hash.
- Raw key appears only once.
- Add copy-to-clipboard button for raw key.
- Add last_used_at and active status.
- Add “Deactivate” confirmation.

If backend does not expose available scopes, add endpoint:

```text
GET /auth/api-key-scopes
```

It should return scope names, category and description.

Acceptance criteria:

- Admin can create least-privilege AI keys safely.

## Phase 7 — Module manifest loader

Build safe, data-only module loader.

Do not execute arbitrary plugin code.

Directory shape:

```text
backend/app/modules/catalog/<module_key>/module.json
backend/app/modules/catalog/<module_key>/services.json
backend/app/modules/catalog/<module_key>/material_templates.json
backend/app/modules/catalog/<module_key>/workflows.json
backend/app/modules/catalog/<module_key>/patient_instructions.json
backend/app/modules/catalog/<module_key>/ai_prompts.json
```

Implement:

- manifest parsing
- validation
- idempotent import/update of Module records
- idempotent import/update of Service records by code
- optional import of material templates by service code + inventory SKU
- no dynamic Python execution

Add command or endpoint:

```text
python -m app.modules.load_catalog
```

or admin-only endpoint:

```text
POST /api/modules/load-catalog
```

Acceptance criteria:

- Gastroenterology module can load services from manifest.
- Running loader twice does not duplicate data.
- Loader has tests.

## Phase 8 — Demo seed and reset command

Add demo-data tooling.

Commands:

```text
python -m app.demo.seed
python -m app.demo.reset
```

Seed should create:

- demo admin/physician/reception/inventory users
- patient
- provider
- room
- services
- appointment for today
- supplier
- inventory items
- stock batches
- service material templates
- purchase order with lines

Reset must be safe:

- only enabled when `APP_ENV != production`
- refuses to run in production
- clearly named demo data

Acceptance criteria:

- Demo environment can be reset before a presentation.
- Real production data cannot be wiped accidentally.

## Phase 9 — Audit timeline for entity detail

Add a reusable audit timeline component.

Backend may need endpoint:

```text
GET /api/audit-log?entity_type=Appointment&entity_id=123
```

If entity_id filtering does not exist, add it.

Frontend:

- show audit timeline on appointment detail
- show audit timeline on invoice detail if feasible
- show actor_type, action, timestamp and summary

Acceptance criteria:

- During demo, user can show traceability of key actions.

## Phase 10 — Pilot runbook

Create:

```text
docs/PILOT_RUNBOOK.md
```

Include:

- how to start local demo
- how to reset demo data
- demo login credentials
- exact demo script
- expected outcomes
- known limitations
- what not to do with real patient data
- rollback/backup reminders

Acceptance criteria:

- A second developer or clinician can run the pilot demo from the document.

## Suggested commit sequence

1. `test: add full pilot demo smoke flow`
2. `feat: add appointment detail page`
3. `feat: refine material consumption workflow ui`
4. `feat: refine purchase receiving workflow ui`
5. `feat: refine invoice issue and payment ui`
6. `feat: harden api key scope management ui`
7. `feat: add safe module manifest loader`
8. `feat: add demo seed and reset commands`
9. `feat: add entity audit timeline`
10. `docs: add pilot runbook`

## Definition of done

Pilot Readiness Sprint is done when:

- full pilot demo smoke test passes
- appointment detail page exists
- material consumption workflow is safe and understandable
- purchase receiving workflow is safe and understandable
- invoice issue/payment workflow is safe and understandable
- API key UI supports least-privilege key creation
- module loader is data-only and idempotent
- demo seed/reset commands exist and are production-safe
- audit timeline exists for appointment detail
- pilot runbook exists

Do not use real patient data. Do not start broad clinical expansion until this demo flow is excellent.
