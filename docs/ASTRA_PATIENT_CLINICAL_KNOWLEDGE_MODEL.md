# ASTRA Patient Clinical Knowledge Model

Status: MVP hardening model, demo/pilot only

## 1. Purpose

Patient Clinical Knowledge is the patient-centered clinical layer of ASTRA Clinic Core.

It answers three questions when a physician opens a patient:

- What do we currently know about this patient?
- What remains unresolved?
- Where did each statement come from?

This model is not a full EMR, guideline engine or medical decision system.

## 2. Why Patient Knowledge Comes Before Episode Engine

Real clinical care is fragmented. A patient may have a consultation in ASTRA, gastroscopy elsewhere, pathology from a hospital, scanned PDFs, laboratory reports, referrals and follow-up notes from different institutions.

ASTRA must first understand the patient-level evidence before organizing that evidence into episodes, workflows or domain reasoning.

Episode Engine remains experimental/deferred until patient-level knowledge and source transparency are stable.

## 3. ClinicalDocument

`ClinicalDocument` is the source object for patient knowledge.

It can represent:

- internal consultation
- internal procedure
- external endoscopy report
- pathology report
- laboratory report
- radiology report
- discharge letter
- referral
- uploaded or scanned document metadata

External documents are first-class clinical inputs, not secondary notes.

## 4. AI Extraction Suggestion

AI extraction is a suggestion layer.

It may produce:

- summary
- key findings
- recommendations

AI extracted knowledge is never official until physician-reviewed.

ClinicalDocument also stores an explicit AI extraction lifecycle:

- `not_run`
- `generated`
- `edited`
- `accepted`
- `rejected`
- `superseded`

`generated` and `edited` remain AI suggestion states. `accepted` only happens through physician review when extraction fields exist. `rejected` keeps extraction output out of official patient knowledge while the raw `ClinicalDocument` source remains available for manual review.

## 5. Physician Review

The physician may edit extracted summary, findings and recommendations before confirming review.

Only after review may the document contribute to the official patient summary.

Rejecting an AI summary rejects the AI extraction/suggestion, not the raw source document. The document returns to a draft source state and can later be manually edited, re-extracted, and reviewed.

ClinicalDocument now stores an explicit `review_status` lifecycle:

- `draft`
- `extracted`
- `needs_physician_review`
- `reviewed`
- `rejected`
- `superseded`

`physician_reviewed` remains as a compatibility field. Official Patient Clinical Knowledge requires both `review_status=reviewed` and `physician_reviewed=true`.

## 6. Official Patient Knowledge

Official patient knowledge is generated only from reviewed Clinical Documents.

It is a structured view, not a separate diagnosis registry.

ASTRA must not display unsourced AI statements as official clinical facts.

Contract tests now lock this rule:

- `review_status=reviewed` and `physician_reviewed=true` are both required.
- AI extraction status alone never makes a statement official.
- `PatientClinicalSummaryRecord` is a summary view, not a source document.
- Rejected and superseded documents do not contribute to official knowledge.

## 7. Source-Linked Summary

Every official summary item must contain at least one source document.

Source badges link to:

`/clinical-documents/{document_id}`

If a candidate item has no source, it is not returned in the official patient summary.

Open questions follow the same source rule. They are displayed as unresolved questions or warnings, not as clinical decisions.

Patient Clinical Summary is a helper view over that source-linked knowledge.

Supported summary statuses are:

- `draft_ai`
- `needs_review`
- `reviewed`
- `stale`
- `rejected`
- `superseded`

Reviewed summaries may become stale when newer reviewed ClinicalDocuments exist. ASTRA reports stale state dynamically and blocks confirmation of stale drafts; the user must regenerate a draft from current reviewed sources.

## 8. Unresolved Findings / Open Questions

Open questions are reviewed, source-linked statements that still need clinical attention.

Examples:

- pathology pending
- follow-up interval needs review
- external report needs reconciliation

They are visible warning/question items, not automatic decisions, tasks, diagnoses or patient-facing instructions.

In the API, open question items may carry display metadata:

- `display_kind=open_question`
- `severity=warning`
- `requires_attention=true`

This metadata is for UI clarity only. It does not create a Task engine, Clinical Readiness Gate or Workflow Engine.

## 9. External Documents And Fragmented Care

ASTRA treats external reports as part of the patient story when they are reviewed.

The source metadata should preserve:

- origin
- institution
- author when known
- document date
- attachment placeholder

## 10. OCR Placeholder Boundary

This sprint does not implement real OCR.

OCR is represented by raw text and attachment metadata only.

Future OCR must still preserve original source inspection and physician review.

## 11. AI Placeholder Boundary

This sprint does not integrate a real AI provider.

The current extraction is a deterministic placeholder that demonstrates the review contract:

AI proposes. Physician confirms. Sources remain visible.

## 12. What Is Deliberately Not Implemented Yet

- real OCR provider
- real AI provider
- autonomous medical decisions
- automatic diagnosis creation
- Workflow Engine
- Knowledge Engine
- new clinical modules
- real patient data enablement
- real Croatian fiscalization

## 13. Future Migration Path

Patient Clinical Knowledge becomes the evidence base for later systems:

- Episode Engine can group reviewed facts into clinical stories.
- Workflow Engine can add operational tasks after the facts are known.
- Knowledge Engine can later reason over reviewed, source-linked facts.
- AI layer can assist, but never replace physician responsibility.

Everything starts from the patient and the source.
