# Current architecture

This is the canonical architecture summary. `docs/ASTRA_ARCHITECTURE_BIBLE.md` remains the highest architectural authority.

## Components and data flow

React/TypeScript/Vite calls a FastAPI REST backend. FastAPI uses SQLAlchemy 2 and Alembic against PostgreSQL. JWT/API-key authentication feeds permission-based RBAC. Important mutations call the shared audit service. Local document storage persists generated relative paths and checksums; original documents remain the source of truth.

`Patient → Appointment → PatientJourney` is the operational spine. A journey references preparation, document requests/submissions, timeline events, check-in, encounter, consumable usage, invoice and payment. The daily dashboard is an aggregate read view; the Patient Journey Workspace mutates existing domain objects through explicit APIs.

## Source-of-truth hierarchy

1. Original source document and human-entered clinical/financial record.
2. Human review state and audited workflow mutation.
3. OCR/classification/AI extraction as derived candidates.
4. UI summaries and dashboard projections.

Derived text never replaces the source. AI suggestions require visible status and individual human action. The absent canonical ICD catalog keeps AI diagnosis suggestions blocked.

## Boundaries

- Document source: MIME/size validation, UUID storage name, resolved-root check, checksum and RBAC.
- AI: backend-only key, explicit feature flag, minimal clinical text, no identifiers, `store:false`, catalog validation and audit; default off.
- Providers: interfaces/stubs are not integrations. Production startup rejects demo/stub modes that could falsely signal OCR, delivery, AI processing or fiscalization.
- Financial state: explicit consumable, invoice and payment actions; no payment terminal or real fiscalization.
- Deployment: Docker Compose is a local/test topology, not a production architecture.
