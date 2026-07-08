# Program 1 Phase D101 Regression Notes

Status: Alembic migration added

## Completed

- `0019_clinical_open_questions.py` migration added after `0018_clinical_findings`
- `clinical_open_questions` table foundation added
- source-linking, status and schema-version check constraints added
- patient, finding, source document and reviewer FK expectations added
- patient, finding, source document, status, question key, source type and created-at indexes added

## Runtime Behavior

No endpoint, service, UI or automatic open-question creation behavior was added.

## Preserved No-Go Areas

- no open question endpoint
- no open question service
- no frontend UI/client action
- no automatic question creation
- no Task, Outcome Evidence or patient messaging
- no diagnosis, treatment, approval, clearance or override
