# Program 1 Phase D94 Regression Notes

Status: persistence safety guards reviewed

## Guard Coverage

Existing open question contract tests verify:

- passive schema forbidden fields remain absent
- safe status vocabulary rejects unsafe status names
- source reference is required
- clinician review is required
- open question runtime routes do not exist
- `ClinicalOpenQuestion` ORM model does not exist
- `clinical_open_questions` metadata table does not exist
- `app/services/clinical_open_questions.py` does not exist

Frontend smoke also verifies:

- no open question client methods
- no `/open-questions` client path
- no open question UI labels in `PatientDetail`

## Decision

Existing guards are sufficient for D94. No additional runtime code or test broadening was needed.

## Preserved No-Go Areas

- no DB model or migration
- no endpoint
- no service
- no frontend client/action
- no automatic question creation
