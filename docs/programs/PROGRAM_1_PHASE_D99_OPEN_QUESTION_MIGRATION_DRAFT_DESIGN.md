# Program 1 Phase D99 - Open Question Migration Draft Design

Status: design before DB foundation

## Migration Intent

Add a passive DB foundation for source-linked open questions. This is not runtime open-question workflow approval.

## Proposed Table And Model

- table name: `clinical_open_questions`
- model name: `ClinicalOpenQuestion`
- migration intent: DB foundation only

## Columns

- `id`
- `patient_id`
- `finding_id`
- `source_document_id`
- `source_type`
- `source_label`
- `source_reference`
- `question_key`
- `label`
- `status`
- `requires_clinician_review`
- `reviewed_at`
- `reviewed_by_user_id`
- `limitations_json`
- `schema_version`
- `created_at`
- `updated_at`

## Constraints

- safe lifecycle status vocabulary only
- non-empty `source_type`
- non-empty `source_label`
- non-empty `source_reference`
- non-empty `question_key`
- non-empty `label`
- non-empty `schema_version`

## Indexes

- `patient_id`
- `finding_id`
- `source_document_id`
- `status`
- `question_key`
- `source_type`
- `created_at`

## Source-Linking Policy

Every row must carry source type, label and reference. `finding_id` and `source_document_id` may be nullable only when the source reference remains explicit.

## Review Metadata Policy

Review metadata fields may exist as passive columns. They must not create a review workflow, physician decision, recommendation, task, outcome evidence or patient communication.

## Explicit Runtime Boundary

- no endpoint
- no service
- no UI
- no automatic question creation
- no Task, Outcome Evidence or patient message
- no automatic diagnosis or treatment
- no production or real-data approval
