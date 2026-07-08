# Program 1 Phase E3 - Review Lifecycle Status Taxonomy

Status: documented

| Status | Definition | Allowed Interpretation | Forbidden Interpretation | Audit Implication |
| --- | --- | --- | --- | --- |
| `not_started` | Review has not begun. | Pending human attention. | No risk or no issue. | none by itself |
| `awaiting_review` | Ready for human review. | Needs human review. | Diagnosis/treatment pending automatically. | future access/review audit candidate |
| `in_review` | Human review is underway. | Review process started. | Decision already made. | future review audit candidate |
| `reviewed` | Human review occurred. | Context was inspected. | Approved, cleared or resolved. | future review audit candidate |
| `needs_clinician_decision` | Review indicates a decision may be needed. | Physician decision boundary. | Automatic decision. | future review audit candidate |
| `decision_documented` | Separate decision has been documented elsewhere. | Link to separate decision concept. | Review itself is the decision. | future audit relation |
| `deferred` | Review is intentionally postponed. | Not completed yet. | Closed or safe. | future audit candidate |
| `closed_for_now` | Review is closed temporarily. | No active review action now. | Permanent closure or outcome proof. | future audit candidate |

## Forbidden Statuses

`approved`, `cleared`, `overridden`, `diagnosed`, `treated`, `patient_notified`, `task_completed`, `outcome_confirmed`, `resolved_by_ai`.
