# Program 1 Phase D81 - Open Question Lifecycle Status Taxonomy

Status: status taxonomy

## Safe Statuses

| Status | Definition | Allowed Interpretation | Forbidden Interpretation | Finding Relationship | Audit Implication |
| --- | --- | --- | --- | --- | --- |
| `draft` | Question is drafted and not ready for official display. | Source review needed. | Not official truth. | May originate from finding context. | Draft creation may be auditable later. |
| `suggested` | Question has been suggested from source/finding context. | Candidate for human review. | Not diagnosis or task. | Finding may suggest it. | Suggestion audit may be useful later. |
| `awaiting_review` | Question needs human review. | Human interpretation pending. | Not blocker or clearance. | Finding remains source context. | Review queue event may be auditable later. |
| `under_review` | Human review is in progress. | Reviewer is evaluating source context. | Not final decision. | Finding may remain unchanged. | Review start may be auditable later. |
| `needs_clinician_decision` | Clinician decision may be required. | Decision is separate. | Not decision itself. | Finding may require interpretation. | Decision request should be auditable later. |
| `decision_documented` | Separate clinician decision has been documented. | Decision exists elsewhere. | Not automatic closure. | Finding may reference separate decision later. | Decision audit required later. |
| `deferred` | Question is deferred with context. | Not resolved. | Not ignored or closed by AI. | Finding remains source-linked. | Deferral reason should be auditable later. |
| `closed_for_now` | Question is closed temporarily with context. | May be reopened. | Not permanent cure or outcome proof. | Finding is not automatically closed. | Closure reason should be auditable later. |

## Forbidden Statuses

- `resolved_by_ai`
- `diagnosed`
- `treated`
- `patient_notified`
- `task_completed`
- `outcome_confirmed`
- `approved`
- `cleared`
- `overridden`

## Runtime Boundary

D81 defines vocabulary only. It does not implement status transitions.

