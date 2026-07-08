# Program 1 Phase D90 - Open Question Source-Linking Persistence Rules

Status: design only

## Rules

- every persisted open question must remain source-linked
- finding relation should be stored when a question comes from a finding
- source document relation should be stored when a source document exists
- extraction candidate relation may be stored as draft provenance only
- source type, source label and source reference should be required
- source text span may be stored later if a safe source-span contract exists
- limitations must be present
- confidence or traceability labels may be added later but must not create official truth

## Invalid Or Draft State

An unlinked question remains invalid or draft. It must not appear as a clinical decision, recommendation, task, outcome evidence or patient communication.

## Human Review Boundary

Source-linked persistence only records traceability. It does not make the question clinically true, resolved or decided. Human interpretation remains required.

## Extraction Boundary

Extraction candidates may suggest question text later, but persistence must not allow extraction to create official clinical truth without human confirmation.
