# Program 1 Phase D12 - Findings Database Shape Review

Status: database shape review

## Proposed Columns

- `id`
- `patient_id`
- `source_document_id` nullable
- `source_type`
- `source_label`
- `source_reference`
- `finding_key`
- `label`
- `category`
- `lifecycle_status`
- `requires_review`
- `reviewed_at`
- `reviewed_by_user_id`
- `limitations`
- `created_at`
- `updated_at`
- `schema_version`

## Forbidden Columns

- `diagnosis_confirmed`
- `treatment_plan`
- `patient_notified`
- `task_id`
- `outcome_evidence_id`
- `approval_status`
- `clearance_status`
- `resolved_by_ai`
- `auto_closed_at`

## Column Policy

- `patient_id` required.
- `source_type`, `source_label`, `source_reference`, `finding_key`, `label`, `category`, `lifecycle_status` required.
- `source_document_id` nullable to support external or future sources.
- `limitations` should be JSON/list shaped.
- `reviewed_at` and `reviewed_by_user_id` nullable until review.
- `requires_review` defaults true for unreviewed or uncertain source-derived findings.

## Indexes

Future migration should consider:

- `patient_id`
- `source_document_id`
- `finding_key`
- `lifecycle_status`
- `requires_review`
- `reviewed_by_user_id`

## FK Expectations

- `patient_id` references `patients.id`
- `source_document_id` references `clinical_documents.id` when present
- `reviewed_by_user_id` references `users.id` when present

## Migration Risks

- premature table creation can imply runtime readiness
- source references may become inconsistent if not designed carefully
- lifecycle status constraints must avoid unsafe statuses
- downgrade must remove table cleanly if migration is later added

## Runtime Boundary

D12 does not add model, migration or endpoint.

