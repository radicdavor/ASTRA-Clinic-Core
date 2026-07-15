# Program 2 — Final Status Matrix

| Capability | Status | Boundary / evidence |
|---|---|---|
| Canonical PatientJourney aggregate | Implemented, tested | One journey per appointment; additive migrations |
| Unified state machine and blockers | Implemented, tested | Guarded transitions and transition events |
| Web intake | Implemented, tested | Shared orchestration; never grants clinical readiness |
| AI secretary intake | Contract/stub, tested | Scoped canonical intake boundary; no live AI vendor |
| Manual intake | Implemented, tested | Same orchestration as other channels |
| Preparation plans and forms | Implemented, tested | Versioned templates, completed-version records and editable requirement review in the workspace |
| Reminders and communication | Implemented with stub delivery, tested | Queued/sent/delivered remain distinct |
| Document ingestion/source storage | Implemented, tested | Original source preserved with checksum and provenance |
| OCR | Provider boundary/stub, tested | Failure states explicit; no external vendor |
| AI document/longitudinal summaries | Provider boundary/stub, tested | Source-linked, labeled, human review required |
| Patient timeline | Implemented, tested | Unified projection with provenance/source links |
| Daily clinic dashboard | Implemented, tested, browser-validated | Four operational columns, one traffic-light state and at most one permission-aware action |
| Reception check-in | Implemented, tested | One-click administrative confirmation; clinical-review items cannot be auto-cleared |
| Unified encounter workspace | Implemented, tested, browser-validated | Interactive check-in, preparation, source review, AI fact review, blocker resolution, encounter and closure operations |
| Consumables | Implemented, tested | FEFO inventory ledger; explicit item/quantity or not-used confirmation |
| Billing/invoice | Implemented, tested | Existing invoice source of truth reused |
| Payment tracking/deferment | Implemented, tested | Direct payment-method actions; authorized auto-closure after explicit resolution |
| Journey closure | Implemented, tested | Preconditions enforced; blockers documented |
| RBAC | Implemented, tested | Least-privilege journey permissions |
| Audit | Implemented, tested | Actor, entity, journey, action and state change evidence |
| Synthetic demo dataset | Implemented, runtime-validated | 12 journeys, three channels, mixed states |
| Alembic migrations | Implemented, tested | Program 2 migrations `0039` through `0045`; PostgreSQL head validated |
| Docker startup | Tested | Database/backend healthy; frontend image built |
| Live email/SMS/mailbox | Deferred, not authorized | Provider contract only |
| Live external OCR/AI | Deferred, not authorized | Provider contract only |
| Payment terminal/fiscalization | Deferred, not authorized | Payment records plus noop fiscalization only |
| Google Cloud/public domains | Deferred, not authorized | Separate deployment/security work required |
| Autonomous clinical decisions | Prohibited | Diagnosis, treatment and procedural clearance remain human-owned |

## Validation summary

- Backend: 476 passed, 9 environment-dependent PostgreSQL tests skipped in the full invocation.
- Frontend: 3 contract tests and 29 DOM interaction tests passed; typecheck, production build and smoke passed.
- PostgreSQL/Alembic: empty database upgraded to head `0046_encounter_findings_opinion`; downgrade to `0045` and re-upgrade validated in Docker.
- Browser: daily dashboard and unified workspace validated using synthetic data.

The skipped PostgreSQL tests are not presented as passes. Runtime PostgreSQL migration and health were validated independently.
