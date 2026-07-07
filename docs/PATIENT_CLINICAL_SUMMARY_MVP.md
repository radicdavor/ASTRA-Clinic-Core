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
- dynamic stale detection
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

Rejecting an AI summary rejects the AI extraction/suggestion only. The original `ClinicalDocument` remains available as a draft source and may later be edited, re-extracted or physician-reviewed.

## Summary Statuses

Patient Clinical Summary supports:

- `draft_ai`: generated AI placeholder draft
- `needs_review`: edited or generated summary awaiting physician review
- `reviewed`: physician-reviewed summary view
- `stale`: summary no longer aligned with newer reviewed documents
- `rejected`: rejected summary, not current
- `superseded`: replaced summary, historical only

Reviewing a stale draft is blocked. The user must generate a new draft from the latest reviewed source documents.

## Source-Linking Principle

Patient Clinical Summary stores `source_document_ids`.

The source-linked structured patient summary also renders source badges for individual reviewed facts. The two views work together:

- concise reviewed summary for orientation
- detailed source-linked facts for traceability

The concise summary is not the source of truth. Reviewed ClinicalDocuments and source-linked knowledge items remain authoritative.

## Open Questions

Open questions are source-linked unresolved items from reviewed ClinicalDocuments.

They are displayed separately from known problems, latest recommendations and the Patient Clinical Summary view.

For UI clarity, open question items expose optional metadata:

- `display_kind=open_question`
- `severity=warning`
- `requires_attention=true`

This metadata does not create tasks, decisions, Clinical Readiness Gate blockers or episode workflow.

## Phase A Hardening Status

Current Phase A hardening adds:

- service extraction for Patient Clinical Knowledge helper logic
- stronger stale summary regression tests
- UI labels that separate official source-linked knowledge, reviewed summary view and AI draft
- conservative AI extraction rejection semantics
- aligned Operational Readiness document review semantics
- documented audit event naming direction
- Phase A5 Open Questions contract, classification tests, display metadata and Patient Workspace separation

This does not make the system production-ready and does not enable real patient data.

## Deferred

- Workflow Engine
- Knowledge Engine
- Episode Engine as primary workflow
- new clinical modules
- real AI provider
- real OCR provider
- real Croatian fiscalization
