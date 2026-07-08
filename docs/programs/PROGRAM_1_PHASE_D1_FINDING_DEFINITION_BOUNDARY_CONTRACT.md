# Program 1 Phase D1 - Finding Definition and Boundary Contract

Status: boundary contract

## Purpose

This contract defines what a finding is and how it differs from nearby Program 1 objects.

## Definitions

| Concept | Definition | Boundary |
| --- | --- | --- |
| Finding | Source-linked clinical knowledge unit that may need review, interpretation or lifecycle tracking. | Not a diagnosis by itself. |
| Source document | Original source object such as ClinicalDocument, report, lab, radiology or pathology document. | Not interpreted clinical knowledge by itself. |
| Extracted text | Text extracted from a source document by manual entry, placeholder extraction or future AI/OCR. | Not official truth until reviewed. |
| Patient Clinical Summary | Summary view over reviewed knowledge and open items. | Not source of truth. |
| Open question | Source-linked unresolved question raised by finding/source context. | Not a task or diagnosis. |
| Recommendation | Possible next clinical direction, draft or suggestion. | Not official until physician confirmed. |
| Physician decision | Human clinical decision documented by authorized clinician. | Separate from the finding itself. |
| Task | Operational action with owner and due date. | Not created automatically by finding. |
| Outcome Evidence | Evidence of what happened after plan, treatment or follow-up. | Not created by finding existence. |
| Patient message | Patient-facing communication. | Not created automatically by finding. |

## Explicit No-Go

A finding is not:

- diagnosis by itself
- treatment plan
- patient instruction
- completed task
- Outcome Evidence
- automatically closed issue
- readiness clearance
- approval
- override

## Safe Interpretation

A finding may indicate that source-linked information requires review.

It does not prove that a clinical action has been taken, a patient has been notified, a task has been completed or an outcome has been documented.

## Runtime Boundary

D1 does not add endpoint, DB model, migration, service or UI behavior.

