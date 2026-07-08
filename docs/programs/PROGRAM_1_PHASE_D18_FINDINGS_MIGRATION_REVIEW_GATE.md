# Program 1 Phase D18 - Findings Migration Review Gate

Status: migration review gate

## Prerequisites Before Migration

- persistence design approved
- database shape reviewed
- source-linking rules accepted
- lifecycle status constraints accepted
- review metadata boundaries accepted
- no-go matrix reviewed
- rollback/downgrade plan reviewed

## Table Naming

Proposed table:

- `clinical_findings`

## FK Policy

Future migration should include:

- `patient_id -> patients.id`
- nullable `source_document_id -> clinical_documents.id`
- nullable `reviewed_by_user_id -> users.id`

## Index Policy

Future indexes should cover:

- patient
- source document
- lifecycle status
- requires review
- finding key

## Constraints

Migration must reject unsafe lifecycle status values and should keep diagnosis/treatment/approval/clearance fields out of the table.

## Downgrade Policy

Downgrade must remove the findings table and related indexes/constraints cleanly.

## Audit And Retention

Audit and retention policy must be defined before runtime writes.

Migration alone does not approve endpoint, service or UI.

## No-Go

Migration gate does not approve:

- runtime endpoint
- write service
- read UI
- Task engine
- Outcome Evidence
- patient messaging
- automatic diagnosis/treatment

