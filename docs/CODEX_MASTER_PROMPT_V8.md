# Codex master prompt v8 — Controlled Pilot Hardening Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect, QA-minded maintainer and product-minded developer.

ASTRA Clinic Core has implemented v7. The project now has:

- appointment detail page
- material consumption workflow on appointment detail
- draft invoice from appointment
- invoice issue/payment UI
- purchase order receiving UI
- API key management UI
- audit timeline component
- entity-level audit filtering
- PostgreSQL-backed pilot demo smoke test
- demo seed command
- demo reset command with production guard
- pilot runbook
- data-only module manifest loader
- release/QA/demo documentation

The project is now demo-ready with demo data only.

The next sprint is:

**Controlled Pilot Hardening Sprint**

Main goal:

Make the closed demo/pilot safe, repeatable, understandable and hard to misuse.

Do not add broad new medical modules yet.
Do not use real patient data.
Do not build real Croatian fiscalization yet.

## Phase 1 — Test module manifest loader

The module loader exists. Now make it trustworthy.

Add tests for:

1. loading one module creates Module record
2. loading the same module twice does not duplicate Module
3. loading services creates Service records by code
4. loading services twice updates existing Service records, no duplicates
5. material templates load by service code + inventory SKU
6. missing inventory item for material template does not crash, but reports skipped template
7. invalid module manifest fails with clear validation error
8. loader never executes arbitrary code

Suggested file:

```text
backend/tests/test_module_manifest_loader.py
```

Acceptance criteria:

- Module loader is idempotent and tested.
- Adding module config is safe.

## Phase 2 — Stabilize pilot demo smoke test

Improve `backend/tests/integration/test_pilot_demo_flow.py`.

Requirements:

- Avoid fixed historical/future dates unless intentionally needed.
- Use `date.today()` or a helper date.
- Avoid hardcoded payment amount if service price can change.
- Read invoice remaining amount before payment.
- Assert audit records for specific key events, not only count.
- Assert material consumption movement type.
- Assert purchase receive movement type.
- Assert invoice fiscalization provider/status/message.
- Assert final inventory value after consume + receive.

Acceptance criteria:

- Pilot demo test remains stable over time.
- Test proves the exact expected workflow, not only approximate counts.

## Phase 3 — Add frontend smoke or Playwright demo test

Add one minimal frontend E2E/smoke test if feasible.

Preferred: Playwright.

Flow:

1. open login
2. login as demo admin
3. open dashboard
4. open appointment detail
5. load material suggestion
6. complete appointment with material consumption
7. create/open invoice
8. issue invoice
9. record payment
10. open purchase orders
11. receive demo purchase order line
12. open audit timeline or audit log

If full Playwright setup is too much, add a lighter frontend smoke test or document why it is deferred.

Acceptance criteria:

- At least one frontend-level check verifies that the main demo UI is not broken.

## Phase 4 — Refine appointment material consumption UX

Improve AppointmentDetail and Dashboard material consumption UI.

Requirements:

- Clearly label material type:
  - required fixed
  - required variable
  - optional
- Show unit of measure.
- Show default quantity.
- Show available stock.
- Show warning if consumption would drop below reorder point.
- Disable confirm if required variable quantity is missing.
- Disable confirm if requested quantity exceeds stock.
- Disable confirm if appointment is already completed/cancelled.
- Refresh related stock movements after success.
- Refresh audit timeline after success.
- Show exact backend error message.

Acceptance criteria:

- A non-developer clinician can understand what will be consumed before confirming.

## Phase 5 — Refine purchase receiving UX

Improve PurchaseOrders page.

Requirements:

- Show supplier, status, total and expected delivery date if available.
- Show ordered/received/remaining per line.
- Default receive quantity to remaining.
- Frontend blocks over-receive.
- LOT required if item has lot tracking enabled.
- Expiration required if item has expiration tracking enabled.
- Disable receive button when no valid line is entered.
- Confirm before receiving stock.
- After receive, refresh purchase order, stock, low-stock and movements if visible.
- Show “partially received” vs “received” clearly.

Acceptance criteria:

- Inventory manager can safely receive a purchase order in demo without curl.

## Phase 6 — Refine invoice issue and payment UX

Improve Invoices page and appointment invoice links.

Requirements:

- Show remaining amount.
- Default payment amount to remaining amount.
- Frontend blocks overpayment.
- Disable payment on draft/cancelled invoices.
- Disable issue if no lines or total <= 0.
- Confirmation before issuing invoice.
- Show visible warning when fiscalization provider is noop/stub:
  - “Demo fiskalizacija — nije stvarna fiskalizacija.”
- Refresh invoice after issue and payment.
- Show payment history if API supports it; otherwise add endpoint if needed.

Acceptance criteria:

- Billing demo can be performed safely and clearly.

## Phase 7 — Harden API key scope UX

Improve API key management.

Backend:

Add endpoint if not present:

```text
GET /auth/api-key-scopes
```

Return:

```json
[
  {"name":"ai.appointments.create", "category":"ai_safe", "description":"Create appointments through AI agent"},
  {"name":"inventory.write_off", "category":"dangerous", "description":"Write off stock"}
]
```

Frontend:

- Group scopes by category:
  - ai_safe
  - read_only
  - operational_write
  - dangerous
- Dangerous scope selection requires confirmation.
- Show warning for billing.mark_paid, inventory.adjust, inventory.write_off, audit.read.
- Add copy-to-clipboard for raw key.
- Raw key shown only once.
- Deactivate requires confirmation.

Acceptance criteria:

- Admin is guided toward least privilege.
- Dangerous scopes are visibly dangerous.

## Phase 8 — Improve audit timeline readability

Audit timeline exists. Make it useful.

Requirements:

- Show action label in human-readable form.
- Show entity type and id.
- Show actor type.
- Show actor user id / API key id if available.
- Show request_id.
- Show timestamp.
- For update actions, provide collapsible before/after JSON or summary diff.
- Add filters on appointment detail if many records.

Backend:

Ensure audit endpoint supports:

- entity_type
- entity_id
- action
- actor_type

Acceptance criteria:

- A demo user can explain what happened and who did it.

## Phase 9 — Add pilot feedback mechanism

Add:

```text
docs/PILOT_FEEDBACK_TEMPLATE.md
```

Include sections:

- participant role
- task attempted
- what worked
- where user got stuck
- confusing labels
- missing data
- unexpected errors
- performance issues
- trust/safety concerns
- must-have before real use
- nice-to-have

Optional:

- GitHub issue template for pilot feedback

Acceptance criteria:

- Pilot feedback can be collected consistently.

## Phase 10 — Real data readiness blocker checklist

Create:

```text
docs/REAL_DATA_READINESS_CHECKLIST.md
```

This document must explicitly state that real patient data is blocked until these are done:

- GDPR/DPIA review
- production hosting decision
- HTTPS
- strong secrets
- user management
- access logging policy
- backup/restore test
- audit retention policy
- incident response plan
- real fiscalization decision
- data processing agreements if hosted externally
- role review
- AI/API key scope review

Acceptance criteria:

- No one can confuse demo readiness with production readiness.

## Phase 11 — Demo mode banner

Add a visible frontend banner when running in demo/development mode.

Requirements:

- Show “DEMO / DEVELOPMENT — do not enter real patient data”
- Read mode from backend health/config endpoint or Vite env
- Banner hidden only in production
- Production should still require safety checks

Acceptance criteria:

- Demo users are visually reminded not to enter real patient data.

## Phase 12 — Pilot runbook refinement

Update `docs/PILOT_RUNBOOK.md`.

Add:

- exact demo duration
- demo personas
- expected screenshots/screens
- fallback if a step fails
- reset command before demo
- known limitations
- feedback collection workflow
- explicit “no real patient data” warning

Acceptance criteria:

- Another person can run the demo without the original developer.

## Suggested commit sequence

1. `test: cover data-only module manifest loader`
2. `test: stabilize pilot demo smoke flow assertions`
3. `test: add frontend pilot smoke test`
4. `feat: refine appointment material consumption ux`
5. `feat: refine purchase receiving ux`
6. `feat: refine invoice payment ux`
7. `feat: harden api key scope ux`
8. `feat: improve audit timeline readability`
9. `docs: add pilot feedback template`
10. `docs: add real data readiness checklist`
11. `feat: add demo mode banner`
12. `docs: refine pilot runbook`

## Definition of done

Controlled Pilot Hardening Sprint is done when:

- module loader has tests
- pilot demo smoke test is stable and specific
- at least one frontend smoke/e2e test exists or a clear deferral is documented
- material consumption UX is safer
- purchase receiving UX is safer
- invoice/payment UX is safer
- API key scope UX guides least privilege
- audit timeline is readable enough for demo
- pilot feedback template exists
- real data readiness checklist exists
- demo mode banner exists
- pilot runbook is detailed enough for another person to run the demo

Do not proceed to real patient data. Do not build broad new modules until controlled pilot feedback is reviewed.
