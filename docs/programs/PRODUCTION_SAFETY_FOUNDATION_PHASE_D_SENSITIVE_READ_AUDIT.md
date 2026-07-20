# Production Safety Foundation — Phase D Sensitive Read Audit

## Status

Implemented as an incremental safety foundation. This does not close the full Production Safety Foundation track.

## Goal

ASTRA must be able to prove intentional access to sensitive patient, clinical, document, report, billing, export, and audit-log surfaces without turning every background refresh into a noisy audit event.

## Model

Phase D uses an explicit interaction endpoint:

```text
POST /api/audit/access-events
```

The endpoint is for intentional UI actions such as opening a patient chart, clinical workspace, signed report, source document, billing detail, export, or audit-log viewer.

Ordinary list loading and automatic refetches remain read-only and are not automatically audited as human access events.

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

## PHI minimization

The access-event payload deliberately excludes free-text notes, patient names, document titles, report text, diagnosis, therapy, laboratory values, and other PHI-rich content.

Stored `after_json` contains only:

- UI surface
- optional clinic ID
- optional journey ID

The auditable object is identified by `entity_type` and `entity_id`.

## Permission

Recording sensitive read events requires:

```text
audit.access_events.write
```

This is separate from `audit.read`. Clinicians, nurses, reception, billing, and document reviewers may record access events without receiving permission to read the audit log.

## Audit-log viewer

Opening `/api/audit-log` is itself audited as:

```text
audit_log.viewed
```

This is intentionally not hidden, because audit-log access is sensitive.

## Remaining work

- Wire frontend intentional-open actions to `POST /api/audit/access-events`.
- Add database-level immutability hardening for `audit_logs` if this becomes a production requirement.
- Add clinic-scoped audit query filters once the audit log carries first-class clinic scope.
