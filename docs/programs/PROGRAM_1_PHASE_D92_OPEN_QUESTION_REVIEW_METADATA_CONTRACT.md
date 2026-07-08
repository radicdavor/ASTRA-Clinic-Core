# Program 1 Phase D92 - Open Question Review Metadata Contract

Status: design only

## Proposed Metadata

- `reviewed_by_user_id`
- `reviewed_at`
- future `review_note` only after separate safety review
- review limitations
- source context visible at review time

## Responsibility Boundary

Physicians may interpret open questions in future workflow design. Nurse and reception roles may see limited context depending on permission design, but should not be treated as final clinical interpreters. API keys, AI agents and system jobs must not perform clinical review.

## What Review Is Not

Review metadata is not:

- diagnosis
- recommendation by itself
- patient instruction
- task creation
- outcome evidence
- patient message
- approval
- clearance
- override

## Future Audit Expectations

If review metadata becomes runtime behavior later, review writes must be audited with actor, timestamp, source context, reason or note boundary, and explicit no-decision semantics. This phase does not implement that workflow.
