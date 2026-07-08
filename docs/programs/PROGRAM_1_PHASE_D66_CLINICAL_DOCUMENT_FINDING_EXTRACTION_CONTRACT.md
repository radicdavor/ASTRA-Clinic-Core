# Program 1 Phase D66 - ClinicalDocument Finding Extraction Contract

Status: extraction contract

## Purpose

Define how a future ClinicalDocument extraction could produce candidate findings without implementing extraction runtime.

This phase does not add OCR, AI provider integration, background jobs, extraction endpoint, finding write service or automatic persistence.

## Definitions

| Concept | Definition | Boundary |
| --- | --- | --- |
| Extraction | A future process that reads source document content and proposes structured candidate data. | Not clinical interpretation by itself. |
| Raw extracted text | Text copied or parsed from a ClinicalDocument source. | Not a finding by itself. |
| Candidate finding | Temporary source-linked proposal derived from source context. | Not persisted official finding, diagnosis, recommendation or decision. |
| Persisted finding | A stored `ClinicalFinding` row with source reference and lifecycle metadata. | Still not diagnosis by itself. |
| Physician-reviewed finding | A finding reviewed in source context by an authorized human under future policy. | Review still does not automatically create treatment, task, outcome or patient message. |

## Relationship to ClinicalDocument

ClinicalDocument is the source object.

Extraction candidates must reference:

- source document id or external source reference
- source type
- source label
- source reference or text span
- extraction method
- limitations

## Relationship to Patient

A candidate may be associated with a patient only through source context. Patient linkage is not clinical truth and does not create a patient-facing instruction.

## Relationship to Lifecycle Status

The only safe initial lifecycle status for a future candidate is `awaiting_review` or equivalent review-needed state.

Extraction cannot set diagnosis, treatment, approval, clearance, resolved or patient-notified states.

## Why Extraction Is Not Diagnosis

Extraction only identifies possible structured information in a source. It does not interpret clinical meaning, reconcile conflicting sources or decide care.

## Why Extraction Is Not Treatment Plan

Extraction cannot prescribe action, schedule follow-up, start treatment, create referral or send patient instructions.

## Why No Runtime Extraction Is Implemented

Runtime extraction remains no-go until source traceability, human review, audit, retention and legal/privacy governance are reviewed separately.

