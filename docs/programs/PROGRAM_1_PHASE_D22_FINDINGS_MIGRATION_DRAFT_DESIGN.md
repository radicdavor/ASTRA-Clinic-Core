# Program 1 Phase D22 - Findings Migration Draft Design

Status: migration draft design

## Intent

Add a DB foundation for findings without exposing any runtime endpoint, service or UI.

## Proposed Shape

- table: `clinical_findings`
- model: `ClinicalFinding`

## Columns

- `id`
- `patient_id`
- `source_document_id`
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
- `limitations_json`
- `schema_version`
- `created_at`
- `updated_at`

## Constraints

- required source text fields must be non-empty
- `schema_version` must be non-empty
- `lifecycle_status` must use the safe D2 vocabulary
- no diagnosis/treatment/approval/clearance fields

## Indexes

- patient
- lifecycle status
- finding key
- category
- source type
- source document
- created at

## No-Go

D22-D32 must not add:

- runtime findings endpoint
- findings service
- frontend UI
- Task engine
- Outcome Evidence
- patient messaging
- automatic diagnosis/treatment
- appointment status mutation
- production or real-data approval

