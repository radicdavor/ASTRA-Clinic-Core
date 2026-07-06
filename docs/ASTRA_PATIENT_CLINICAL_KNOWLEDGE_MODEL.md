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

## 5. Physician Review

The physician may edit extracted summary, findings and recommendations before confirming review.

Only after review may the document contribute to the official patient summary.

Rejecting a summary keeps it out of official patient knowledge.

## 6. Official Patient Knowledge

Official patient knowledge is generated only from reviewed Clinical Documents.

It is a structured view, not a separate diagnosis registry.

ASTRA must not display unsourced AI statements as official clinical facts.

## 7. Source-Linked Summary

Every official summary item must contain at least one source document.

Source badges link to:

`/clinical-documents/{document_id}`

If a candidate item has no source, it is not returned in the official patient summary.

## 8. Unresolved Findings / Open Questions

Open questions are reviewed, source-linked statements that still need clinical attention.

Examples:

- pathology pending
- follow-up interval needs review
- external report needs reconciliation

They are operational warnings, not automatic decisions.

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
