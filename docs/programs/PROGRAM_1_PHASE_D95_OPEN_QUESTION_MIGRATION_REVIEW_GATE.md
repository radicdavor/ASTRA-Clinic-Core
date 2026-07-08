# Program 1 Phase D95 - Open Question Migration Review Gate

Status: future migration prerequisite

## Prerequisites Before Migration

- approved source-linking constraints
- approved safe status constraint list
- review metadata policy
- audit and retention policy
- rollback strategy
- backup/restore review
- route/service/UI no-go guards remain green
- production and real-data no-go remains explicit

## Table Naming

Future table name: `clinical_open_questions`.

Future model name: `ClinicalOpenQuestion`.

## FK Policy

- required `patient_id`
- nullable `finding_id`
- nullable `source_document_id`
- nullable `reviewed_by_user_id`

No FK should link to Task, Outcome Evidence, patient message, appointment status, approval, clearance or override entities.

## Index Policy

Indexes should support patient-scoped reads and review filtering without implying workflow automation:

- `patient_id`
- `status`
- `question_key`
- `finding_id`
- `source_document_id`
- `requires_clinician_review`
- `created_at`

## Constraints

Future migration should enforce:

- safe status vocabulary
- non-empty `source_type`
- non-empty `source_label`
- non-empty `source_reference`
- non-empty `question_key`
- non-empty `label`
- non-empty `schema_version`
- clinician review required by default

## Rollback And Restore

Downgrade must remove the open question table and indexes without mutating patients, findings, clinical documents, snapshots or acknowledgments. Backup/restore implications require separate production review.

## Explicit Non-Goals

- no runtime endpoint
- no UI
- no write service
- no Task, Outcome Evidence or patient messaging
- no automatic diagnosis or treatment
- no production or real-data approval
