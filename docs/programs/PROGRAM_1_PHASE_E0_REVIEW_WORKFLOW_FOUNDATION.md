# Program 1 Phase E0 - Review Workflow Foundation

Status: opened, documentation-first

## Why Phase E Exists

Phase D created source-linked findings, extraction candidates and open question read surfaces. Phase E defines what human review means before any review endpoint, persistence model, service or UI action is allowed.

## What Review Is

Review is human inspection of source-linked clinical context. It may involve a ClinicalDocument, Finding, Open Question or Extraction Candidate. Review preserves the source reference and records that the material needs or received human interpretation.

## What Review Is Not

Review is not approval, clearance, override, diagnosis, treatment plan, Task, Outcome Evidence, patient message, appointment status change or automatic closure.

## Relationships

- ClinicalDocument: review may inspect the document and source sections.
- Finding: review may inspect source-linked finding context.
- Open Question: review may inspect an unresolved source-linked question.
- Extraction Candidate: review may inspect a non-persisted candidate, but does not make it official truth.
- Physician decision: review may precede a separate physician decision.
- Recommendation: review may inform a future recommendation draft, but is not one by itself.
- Task, Outcome Evidence, patient messaging: no runtime relation in Phase E.

## Runtime Boundary

E0 does not introduce endpoint, DB model, migration, service, UI, permission seed or audit event.

## Deployment Boundary

Demo/pilot-only assumptions continue. Production and real patient data remain no-go.
