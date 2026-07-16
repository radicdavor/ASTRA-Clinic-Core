# Phase A — Current state, pilot boundary and evidence-gap audit

Audit baseline: repository `radicdavor/ASTRA-Clinic-Core`, branch `main`, starting commit `bd0b78f`. The worktree was clean and aligned with `origin/main`. No real-data pilot, production deployment or conflicting readiness track was active.

## Capability inventory

| Capability | Classification | Current evidence / gap |
|---|---|---|
| Canonical PatientJourney workflow | IMPLEMENTED | One journey joins appointment, preparation, documents, check-in, encounter, consumables, invoice and payment. |
| Daily dashboard and role-aware navigation | IMPLEMENTED BUT NOT PILOT-VALIDATED | Automated and Codex browser evidence exists; no human participant evidence. |
| Patient Journey Workspace | IMPLEMENTED BUT NOT PILOT-VALIDATED | Stage-focused UI and source-linked context exist. |
| Manual intake | IMPLEMENTED | Shared journey creation path. |
| Web and AI-secretary intake concepts | CONTRACT ONLY | API/domain boundaries exist; no live public or assistant integration. |
| Local document upload/source viewing | IMPLEMENTED | MIME/size checks, generated storage name, checksum, path boundary and RBAC exist. |
| Reception scan | IMPLEMENTED BUT NOT PILOT-VALIDATED | Browser upload labelled as scan; no hardware scanner driver. |
| OCR | STUBBED | Deterministic text-only local demo provider; PDF/image OCR fails explicitly. |
| Classification | STUBBED | Metadata-only local candidate; human review required. |
| AI longitudinal summary | STUBBED | Deterministic local source index; not an external model. |
| AI diagnosis suggestions | DISABLED | Explicit flag defaults off; no canonical ICD catalog; pilot blocked. |
| E-mail/SMS reminders | STUBBED | Queue and demo sender record `sent`, never `delivered`; no provider. |
| Mailbox ingestion | CONTRACT ONLY | Envelope/manual-review boundary only. |
| Billing/payment workflow | IMPLEMENTED BUT NOT PILOT-VALIDATED | Local financial mutations and audit exist; no fiscalization or payment terminal. |
| Fiscalization | STUBBED | `noop`/Croatia stub only; production startup rejects them. |
| Audit | IMPLEMENTED BUT NOT PILOT-VALIDATED | Meaningful workflow events are recorded; retention/governance not approved. |
| RBAC | IMPLEMENTED BUT NOT PILOT-VALIDATED | Permission checks and tests exist; clinic owner approval is absent. |
| Alembic/PostgreSQL CI | IMPLEMENTED | PostgreSQL service, unique head and migration boundary gate. |
| Backup/restore drill | IMPLEMENTED BUT NOT PILOT-VALIDATED | Synthetic test-only script; no production backup policy. |
| Monitoring/alerting | NOT IMPLEMENTED | Health endpoint exists; no operational alerting. |
| Incident response | DEFERRED | Runbook created by this track; no staffed response organization. |
| Privacy/processor governance | NOT AUTHORIZED | No DPA, DPIA, retention approval or processor acceptance. |
| Real patient data | NOT AUTHORIZED | `REAL_DATA_ALLOWED=false`; demo banner required. |
| Production deployment/go-live | NOT AUTHORIZED | No production deployment or clinical-use approval. |

## Mutations and boundaries

Clinical mutations are encounter notes, explicit diagnosis acceptance, document review, check-in clinical review and encounter completion. Financial mutations are consumable confirmation, invoice issue, payment and closure. Destructive actions remain confirmation/audit protected. External-network code is limited to the disabled AI diagnosis provider boundary; no key or flag alone is sufficient and no patient identifier is accepted by its request schema.

## Only authorized candidate

**Controlled Internal Synthetic Clinic Pilot**: synthetic patients, local/controlled test environment, manual or pre-existing appointment, local upload/source review, local OCR stub, local source-linked summary, no live communication or external integration. It excludes real PHI/PII, public booking, AI secretary, mailbox, scanner driver, live OCR, SMS, e-mail, fiscalization and production.

Pilot readiness does not authorize pilot execution.
