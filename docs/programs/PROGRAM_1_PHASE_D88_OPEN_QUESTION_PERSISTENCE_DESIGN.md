# Program 1 Phase D88 - Open Question Persistence Design

Status: design only

## Proposed Persistence Surface

- proposed entity name: `ClinicalOpenQuestion`
- proposed table name: `clinical_open_questions`
- scope: patient-scoped, source-linked unresolved clinical question
- implementation status: not implemented in this phase

## Relationships

- patient: required future relation; every persisted question must belong to one patient
- finding: optional future relation; links a question to the finding that suggested it when available
- source document: optional future relation; links the question to the source document when available
- extraction candidate: optional future reference; records draft provenance without making extraction official truth
- source reference: required future text/reference field that keeps the question traceable

## Proposed Persistence Rules

- `source_type`, `source_label` and `source_reference` should be stored with the question
- status should use the safe open question lifecycle vocabulary
- limitations should be stored because the question is not a clinical decision
- review metadata may be stored later but must not create a review workflow by itself
- source-linked persistence must not rewrite findings, source documents or extraction candidates

## Forbidden Links

- no Task link
- no Outcome Evidence link
- no patient message link
- no appointment status link
- no diagnosis confirmation field
- no treatment plan field
- no approval, clearance or override field

## Why No DB Model Or Migration Yet

This phase clarifies persistence shape before any table exists. A later migration phase must review source-linking, status constraints, review metadata, audit retention, rollback and privacy before adding a DB model or Alembic revision.

## Production And Real-Data Boundary

Persistence design does not approve production use or real patient data. Open questions remain demo/pilot governance artifacts until explicit production and privacy review is complete.
