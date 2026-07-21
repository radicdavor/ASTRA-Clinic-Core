# Production Safety Foundation — Phase D Sensitive Read Audit

## Status

Implemented and then hardened as an incremental safety foundation. This does not close the full Production Safety Foundation track.

## Goal

ASTRA must be able to prove intentional access to sensitive patient, clinical, document, report, billing, export, and audit-log surfaces without turning every background refresh into a noisy audit event.

## Model

Phase D uses an explicit interaction endpoint:

```text
POST /api/audit/access-events
```

The endpoint is for intentional UI actions such as opening a patient chart, clinical workspace, signed report, source document, billing detail, or report viewer.

Ordinary list loading and automatic refetches remain read-only and are not automatically audited as human access events.

## Hardened backend contract

The client may submit only:

- controlled action code
- controlled entity type
- entity ID
- controlled UI surface
- optional interaction ID for duplicate-click suppression

The client may not submit:

- actor identity
- clinic ID
- journey ID
- event timestamp
- arbitrary metadata
- patient names, document titles, diagnosis, therapy, laboratory values, or other PHI-rich text

Object scope is resolved by the backend from the current authenticated user, active clinic, and database relationships. Cross-clinic objects return `404` without disclosing whether the object exists elsewhere.

## Controlled event set

The backend accepts only these read/access event actions:

- `patient.viewed`
- `clinical_workspace.opened`
- `clinical_form.viewed`
- `signed_report.viewed`
- `source_document.viewed`
- `source_document.downloaded`
- `billing_details.viewed`
- `patient_export.created`
- `clinical_report.printed`
- `audit_log.viewed`

The backend validates that each action matches an allowed entity type. For example, `signed_report.viewed` may not be recorded against a `Patient`.

`patient_export.created` is intentionally not accepted through the generic direct endpoint. It must be emitted from a future approved export workflow so the export operation and audit event remain tied together.

## Permission

Recording sensitive read events requires:

```text
audit.access_events.write
```

The event also requires the permission needed for the underlying sensitive surface. Examples:

- `patient.viewed` requires `patients.read`
- `source_document.downloaded` requires `documents.view_source`
- `billing_details.viewed` requires `billing.read`
- `clinical_report.printed` requires `reports.print`

This keeps the write-only audit endpoint from becoming a cross-surface existence oracle.

## PHI minimization

Stored `after_json` contains only:

- UI surface
- backend-resolved clinic ID
- optional interaction ID

The auditable object is identified by `entity_type` and `entity_id`.

## Idempotency

If the same actor records the same action, entity, and `interaction_id` more than once, the backend returns the first audit row instead of creating duplicates. This is for duplicate clicks and client retries, not for merging distinct clinical accesses.

## Audit-log viewer

Opening `/api/audit-log` is itself audited as:

```text
audit_log.viewed
```

This is intentionally not hidden, because audit-log access is sensitive.

## Remaining work

- Wire all frontend intentional-open actions to `POST /api/audit/access-events`.
- Add database-level immutability hardening for `audit_logs` if this becomes a production requirement.
- Add first-class clinic scope to audit-log query results if production audit partitioning is required.
