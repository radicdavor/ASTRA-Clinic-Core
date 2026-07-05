# Codex master prompt v6 — Operational Closure Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

---

You are a senior full-stack architect and product-minded developer.

ASTRA Clinic Core has implemented v5. The project now has:

- CI with PostgreSQL service
- Alembic migration step in CI
- backend pytest
- frontend typecheck and build
- SQLite unit test fixture
- PostgreSQL test fixture via `TEST_DATABASE_URL`
- appointment/inventory/procurement/billing tests
- appointment material rollback test
- fiscalization provider boundary integrated into invoice issuing
- production safety checks for weak JWT secret and unsafe CORS
- security/deployment/backup docs
- frontend operational gap analysis
- initial module manifest for gastroenterology

The project is now past the raw MVP stage.

The next sprint is:

**Operational Closure Sprint**

Main goal:

Turn ASTRA Clinic Core from a backend-heavy MVP into a more usable and better-proven clinic operations MVP.

Do not start broad new medical modules or new AI agents yet.

## Guiding principle

Close the loop between:

1. backend domain correctness
2. API-layer permission/audit proof
3. PostgreSQL-backed integration confidence
4. UI workflows that a clinic user can actually operate

## Phase 1 — prove PostgreSQL integration coverage

The project has a `pg_db` / `pg_client` fixture. Now ensure critical tests actually use it.

Add PostgreSQL-backed integration tests for:

1. Alembic migration smoke
2. invoice number sequence with `with_for_update`
3. FEFO consumption using PostgreSQL
4. purchase receiving rollback using PostgreSQL
5. appointment complete-with-consumption rollback using PostgreSQL
6. stock transfer with merge behavior using PostgreSQL
7. production constraints that may differ from SQLite

Suggested files:

```text
backend/tests/integration/test_pg_migrations.py
backend/tests/integration/test_pg_inventory.py
backend/tests/integration/test_pg_procurement.py
backend/tests/integration/test_pg_billing.py
backend/tests/integration/test_pg_appointment_materials.py
```

Acceptance criteria:

- Tests using `pg_db`/`pg_client` run in CI.
- SQLite-only assumptions do not hide PostgreSQL bugs.
- CI fails if PostgreSQL integration tests fail.

## Phase 2 — API-level permission and AI key tests

Service-level tests are not enough.

Add HTTP endpoint tests that prove the real request path:

`HTTP -> auth/API key -> permission -> route -> service -> DB -> audit`

Required tests:

1. unauthenticated request returns 401
2. limited user without `inventory.adjust` cannot call `/api/inventory/adjustment`
3. limited user without `inventory.write_off` cannot call `/api/inventory/write-off`
4. limited user without `billing.mark_paid` cannot mark invoice paid
5. user without `audit.read` cannot read `/api/audit-log`
6. admin can create API key
7. raw API key is returned only once on creation
8. API key hash is never returned
9. AI-scoped API key can call allowed AI endpoint
10. AI-scoped API key cannot call stock adjustment
11. AI-scoped API key cannot call write-off
12. AI-scoped API key cannot mark invoice paid
13. AI-scoped API key cannot read audit log
14. API key actor is stored correctly in audit when it performs an allowed action

Suggested file:

```text
backend/tests/integration/test_api_permissions.py
```

Acceptance criteria:

- AI agent cannot perform destructive or financial actions.
- Permissions are proven through endpoints, not only service functions.

## Phase 3 — API-level workflow tests

Add endpoint tests for full workflows.

### Appointment API

Test:

- create appointment
- reject overlap by provider
- reject overlap by room
- update appointment revalidates conflict
- cancelled appointment does not block slot
- schedule/day ordering
- audit create/update/delete

### Inventory API

Test:

- create item
- create batch with LOT/expiration validation
- write-off requires reason
- adjustment requires reason
- transfer requires reason
- transfer preserves stock
- recalculate stock endpoint fixes cache
- low-stock and expiring endpoints
- audit movement creation

### Appointment material consumption API

Test:

- fixed required material is consumed
- variable required material must be provided
- optional material is not consumed unless provided
- insufficient stock returns 409
- failed consumption leaves appointment status unchanged
- failed consumption creates no stock movements
- successful completion creates movements and marks appointment completed

### Procurement API

Test:

- create PO
- add PO line
- partial receive
- full receive
- over-receive returns 409
- missing LOT/expiration returns 422 when required
- receive action creates batch and movement
- receive action updates current stock
- receive action is audited

### Billing API

Test:

- draft invoice from appointment
- repeated draft does not duplicate
- issue invoice
- invoice number generated on issue
- fiscalization Noop is applied
- add payment
- overpayment returns 409
- mark-paid requires permission
- payment action is audited

Acceptance criteria:

- Daily business workflows are proven through real API endpoints.

## Phase 4 — audit reconstruction quality

Audit must be reliable enough to reconstruct critical events.

Add tests for:

1. patient update has before_json and after_json
2. appointment update has before_json and after_json
3. inventory write-off has before/after and reason
4. stock transfer audits source batch and movements
5. purchase receive audits batch and movement
6. invoice issue audits before/after
7. payment transaction audit exists
8. API key action has actor_type `api_key`
9. request_id is captured when `X-Request-ID` is supplied
10. audit filtering by entity_type/action/actor_type works

Acceptance criteria:

- A critical mutation can be reconstructed from audit records.

## Phase 5 — frontend workflow 1: complete appointment with material consumption

Implement guided UI for completing an appointment with material consumption.

User flow:

1. User opens appointment detail or daily schedule action.
2. Clicks “Završi uz potrošnju materijala”.
3. UI calls suggested material consumption endpoint.
4. UI displays required, optional and variable materials.
5. User can edit quantities where allowed.
6. Required variable material must be entered.
7. UI shows stock warnings.
8. User confirms.
9. UI calls complete-with-consumption endpoint.
10. UI shows success and updated status.

Acceptance criteria:

- A clinician can complete a service and deduct material without curl.
- Backend errors are displayed clearly.
- Dangerous action requires confirmation.

## Phase 6 — frontend workflow 2: purchase order receiving

Implement operational receiving UI.

User flow:

1. User opens purchase order detail.
2. UI shows ordered, received and remaining quantities per line.
3. User enters received quantity per line.
4. If item requires LOT/expiration, UI requires it.
5. User selects stock location.
6. User confirms receive.
7. UI calls receive endpoint.
8. UI shows new status: partially_received or received.

Acceptance criteria:

- Purchase receiving works by line.
- Remaining quantities are clear.
- Over-receive is prevented or clearly rejected.
- Received stock appears in inventory.

## Phase 7 — frontend workflow 3: invoice issue and payment

Implement invoice operational UI.

User flow:

1. From appointment detail, user clicks “Kreiraj nacrt računa”.
2. UI opens invoice detail.
3. User can add/edit lines while draft.
4. User clicks “Izdaj račun”.
5. UI shows official invoice number and fiscalization status/message.
6. User records payment.
7. UI updates payment status.

Acceptance criteria:

- Appointment can be turned into invoice through UI.
- Invoice can be issued through UI.
- Payment can be recorded through UI.
- Fiscalization Noop/stub status is visible.

## Phase 8 — API key management UI

Add minimal admin UI for API keys.

Requirements:

- list API keys without showing key_hash
- create API key with selected scopes
- show raw API key only once after creation
- deactivate API key
- show last_used_at
- warn about least-privilege scopes

Acceptance criteria:

- AI agent key can be managed without curl.
- Secret is not re-displayed after creation.

## Phase 9 — module manifest loader foundation

Build safe data-only module loader.

Current state includes at least a gastroenterology module manifest. Extend carefully.

Directory shape:

```text
backend/app/modules/catalog/<module_key>/module.json
backend/app/modules/catalog/<module_key>/services.json
backend/app/modules/catalog/<module_key>/material_templates.json
backend/app/modules/catalog/<module_key>/workflows.json
backend/app/modules/catalog/<module_key>/patient_instructions.json
backend/app/modules/catalog/<module_key>/ai_prompts.json
```

Rules:

- Do not execute arbitrary plugin code.
- Manifest loading must be idempotent.
- Services can be inserted or updated by code/key.
- Material templates can be inserted or updated by service code + item SKU.
- Workflows are stored as data/config only.

Initial modules:

- gastroenterology
- endoscopy
- dermatology_aesthetics

Acceptance criteria:

- New service catalog can be loaded from manifest.
- Adding a module does not require core model changes.
- Loader has tests.

## Phase 10 — release discipline

Add project maintainer discipline.

Create:

- `CHANGELOG.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/MANUAL_QA_CHECKLIST.md`
- `docs/DEMO_DATA_POLICY.md`

Release checklist must include:

- migrations pass
- backend tests pass
- frontend build passes
- PostgreSQL integration tests pass
- backup/restore reviewed
- default credentials changed before production
- production safety settings reviewed
- audit and RBAC reviewed

Acceptance criteria:

- Project can start behaving like a maintained open-source product.

## Suggested commit sequence

1. `test: add postgres-backed integration coverage`
2. `test: cover api permission and ai key boundaries`
3. `test: cover api appointment inventory procurement billing workflows`
4. `test: cover audit reconstruction and request id`
5. `feat: add appointment completion material consumption ui`
6. `feat: add purchase order receiving ui`
7. `feat: add invoice issue and payment ui`
8. `feat: add api key management ui`
9. `feat: add data-only module manifest loader`
10. `docs: add release changelog and manual qa discipline`

## Definition of done

Operational Closure Sprint is done when:

- PostgreSQL integration tests cover critical domain workflows
- API-layer permission and AI key tests pass
- audit reconstruction tests pass
- three core UI workflows are operational
- API key management UI exists
- module manifest loader is data-only and tested
- release/checklist documentation exists

Do not expand to broad AI automation or many new medical modules until this is complete.
