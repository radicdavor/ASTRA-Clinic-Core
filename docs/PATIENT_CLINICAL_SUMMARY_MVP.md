# Patient Clinical Summary MVP

Status: implemented foundation

## What It Does

Patient Clinical Summary gives the physician a concise patient-level overview from reviewed Clinical Documents.

It supports:

- AI placeholder draft generation
- physician editing
- physician confirmation
- source document IDs
- reviewed/draft status
- Patient Workspace display

## What It Does Not Do

It does not:

- create diagnoses automatically
- replace reading original source documents
- call a real AI provider
- perform OCR
- automate workflow
- calculate clinical guidelines
- enable real patient data

## OCR Deferred

OCR is not implemented in this MVP.

Uploaded/scanned documents may contain manually entered raw text or placeholder text. Future OCR must keep original source inspection and physician review.

## AI Review Safety Rules

AI output is draft-only.

The physician must review, edit if needed and confirm before the summary becomes official.

Unreviewed AI extraction must not be treated as clinical truth.

## Source-Linking Principle

Patient Clinical Summary stores `source_document_ids`.

The source-linked structured patient summary also renders source badges for individual reviewed facts. The two views work together:

- concise reviewed summary for orientation
- detailed source-linked facts for traceability

## Deferred

- Workflow Engine
- Knowledge Engine
- Episode Engine as primary workflow
- new clinical modules
- real AI provider
- real OCR provider
- real Croatian fiscalization
