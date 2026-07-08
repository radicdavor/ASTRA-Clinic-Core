# Program 1 Phase F0 - Clinical Evidence Timeline Foundation

Status: opened, documentation-first

## Why Phase F Exists

Phase D created source-linked findings, open questions, extraction candidates and read surfaces. Phase E defined review semantics. Phase F defines a read-only Clinical Evidence Timeline integration concept that can connect these objects without creating workflow enforcement.

## What Clinical Evidence Timeline Is

Clinical Evidence Timeline is a source-linked, read-only integration view of clinical context events. It can show that a document was received, a finding was recorded, an open question is awaiting review, a review is pending, a snapshot was captured or an acknowledgment was recorded.

## What Timeline Is Not

Timeline is not a workflow engine, diagnosis, treatment plan, Task, Outcome Evidence, patient message, physician decision, approval, clearance, override or appointment status change.

## Relationships

- Patient Clinical Knowledge Layer: timeline is a display/integration concept inside that layer.
- ClinicalDocument: document receipt/review-pending events may appear.
- Findings: source-linked finding lifecycle events may appear.
- Open Questions: source-linked unresolved question events may appear.
- Extraction Candidates: passive candidate events may appear only as non-official context.
- Review: passive review status events may appear as non-decision context.
- Readiness Snapshot and Acknowledgment: snapshot/acknowledgment events may appear as advisory context.
- Audit events: access audit may appear only as security/access context, not clinical outcome evidence.

## Runtime Boundary

F0 does not introduce endpoint, DB model, migration, service, frontend UI, permission seed or audit write.

## Deployment Boundary

Demo/pilot-only assumptions continue. Production and real patient data remain no-go.
