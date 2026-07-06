# Patient Clinical Knowledge Layer MVP

Status: implemented foundation with hardening

## What Works Now

- ClinicalDocument registry for internal, external, scanned and uploaded documents.
- Upload metadata and raw text placeholder.
- OCR placeholder boundary through stored raw text.
- AI extraction placeholder for summary, findings and recommendations.
- Explicit AI extraction lifecycle metadata: `ai_extraction_status`, `ai_extraction_generated_at`, `ai_extraction_updated_at`.
- Editable extraction review before physician confirmation.
- Physician review and summary rejection.
- Explicit ClinicalDocument `review_status` with `physician_reviewed` retained for compatibility.
- Patient Workspace clinical knowledge summary and right sidebar.
- Source badges from every summary item to the original document.
- Documents awaiting review warning in readiness.
- Deep link from readiness to `/clinical-documents?review_status=needs_physician_review`.

## What Is Placeholder

- OCR engine is not implemented.
- AI provider integration is not implemented.
- Attachment storage is represented by local placeholder paths.
- Summary extraction uses simple deterministic rules for demo/pilot flow.

## Physician Review

AI extraction is never official by itself.

The physician can edit:

- AI summary
- key findings
- recommendations

After confirmation, the document becomes eligible for the official Patient Clinical Summary.

Rejecting the summary removes extracted structured items from official knowledge.

Official knowledge requires `review_status=reviewed` and `physician_reviewed=true`. Draft, needs-review, rejected and superseded documents do not feed the official patient knowledge view.

AI extraction status is separate from document review status:

- `generated` and `edited` are suggestions.
- `accepted` means extraction fields were accepted through physician review.
- `rejected` means the AI suggestion was rejected.
- `not_run` is valid for manually reviewed documents without AI extraction.

## Source Rule

Every official Patient Clinical Summary item must have at least one ClinicalDocument source.

Unsourced items must not be returned by the API or displayed as official knowledge.

Duplicate statements are merged inside the same category and their source badges are combined.

## UI Overview

- `/clinical-documents` lists documents and supports review filtering.
- `/clinical-documents/:id` is the document review workspace.
- `/patients/:id` shows clinical knowledge first, with source-linked items and open questions.
- Readiness routes unreviewed document warnings to the filtered document list.

## Deferred

- real OCR
- real AI
- autonomous clinical decisions
- diagnosis registry
- Workflow Engine
- Knowledge Engine
- new clinical modules
- real patient data
- real Croatian fiscalization
- Episode Engine as primary workflow
