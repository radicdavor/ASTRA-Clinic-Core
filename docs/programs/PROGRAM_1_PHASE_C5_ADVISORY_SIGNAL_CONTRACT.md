# Program 1 Phase C5 - Advisory Signal Contract

Status: design-only advisory signal contract

## Purpose

Advisory signals are non-blocking, source-linked readiness warnings for human review.

They are not decisions.

## Contract Fields

Recommended fields:

- `signal_key`
- `label`
- `severity`
- `category`
- `source_type`
- `source_reference`
- `explanation`
- `limitations`
- `snapshot_id`
- `created_at`
- `is_decision`
- `not_decision_disclaimer`

## Severity

Allowed severity:

- info
- warning
- review_required
- missing_input

Severity must not mean workflow block.

## Source

Source may reference:

- live preview item
- snapshot item
- ClinicalDocument
- appointment context

## Forbidden Fields

Do not use:

- approval_status
- clearance_status
- override_status
- enforcement_result
- approved
- cleared
- patient_ready
- procedure_approved
- task_id
- outcome_evidence_id

## Disclaimer

Every advisory signal must remain a non-decision signal.

## Recommended Next Task

`Program 1 Phase C6 - Advisory Signal Backend Type Prototype`
