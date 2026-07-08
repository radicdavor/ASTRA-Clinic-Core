# Program 1 Phase D89 - Open Question Database Shape Review

Status: design only

## Proposed Columns

- `id`
- `patient_id`
- `finding_id` nullable
- `source_document_id` nullable
- `source_type`
- `source_label`
- `source_reference`
- `question_key`
- `label`
- `status`
- `requires_clinician_review`
- `reviewed_at`
- `reviewed_by_user_id`
- `limitations`
- `created_at`
- `updated_at`
- `schema_version`

## Forbidden Columns

- `task_id`
- `outcome_evidence_id`
- `diagnosis_confirmed`
- `treatment_plan`
- `patient_message_id`
- `approval_status`
- `clearance_status`
- `resolved_by_ai`
- `auto_closed_at`
- `patient_notified_at`

## Nullable Policy

`patient_id`, `source_type`, `source_label`, `source_reference`, `question_key`, `label`, `status`, `requires_clinician_review`, `limitations`, `created_at`, `updated_at` and `schema_version` should be required in a future migration. `finding_id`, `source_document_id`, `reviewed_at` and `reviewed_by_user_id` may be nullable.

## Indexes

Future indexes should consider `patient_id`, `finding_id`, `source_document_id`, `status`, `question_key`, `requires_clinician_review` and `created_at`.

## FK Expectations

- `patient_id` should reference patients
- `finding_id` should reference clinical findings if the findings table remains stable
- `source_document_id` should reference clinical documents if available
- `reviewed_by_user_id` should reference users when review metadata is implemented

## Policy Notes

Source-linking fields are required because a persisted question without traceable source context is unsafe. Status values must use the safe open question taxonomy. Review metadata must not imply diagnosis, recommendation, task completion, outcome evidence or patient notification.

## Migration Risks

The first migration must validate source-linking constraints, status constraints, rollback behavior, retention policy and audit implications before implementation. Downgrade must remove the table without touching findings, source documents or patients.
