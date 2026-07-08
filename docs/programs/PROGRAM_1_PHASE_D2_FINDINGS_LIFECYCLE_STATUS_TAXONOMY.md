# Program 1 Phase D2 - Findings Lifecycle Status Taxonomy

Status: status taxonomy

## Purpose

This taxonomy defines safe lifecycle status vocabulary for future findings work.

Statuses are lifecycle and review signals. They are not clinical approval, readiness clearance, diagnosis, treatment, Task completion or Outcome Evidence.

## Safe Statuses

| Status | Definition | Allowed Transition Source | Allowed Transition Target | Who May Interpret It | Audit Implication | Forbidden Interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| `received` | Finding candidate has been received from source context. | none / source import | `linked_to_patient`, `awaiting_review` | System/human reviewer | Candidate creation may be audit-relevant later | Not reviewed or true by itself |
| `linked_to_patient` | Finding candidate is associated with a patient. | `received` | `awaiting_review` | Authorized staff | Link event may be audit-relevant later | Not diagnosis |
| `awaiting_review` | Finding needs human review. | `received`, `linked_to_patient` | `review_in_progress`, `reviewed` | Clinician/reviewer | Review queue event may be audit-relevant later | Not task or clearance |
| `review_in_progress` | Human review has started. | `awaiting_review` | `reviewed`, `needs_clinician_decision` | Reviewer/physician | Review start may be audit-relevant later | Not final decision |
| `reviewed` | Finding has been reviewed as source-linked context. | `review_in_progress`, `awaiting_review` | `needs_clinician_decision`, `closed_for_now`, `follow_up_recommended` | Physician or authorized reviewer by future policy | Review completion should be auditable if implemented | Not diagnosis automatically |
| `needs_clinician_decision` | Finding needs explicit clinician decision. | `reviewed`, `review_in_progress` | `decision_documented` | Physician | Decision request should be auditable if implemented | Not blocking workflow automatically |
| `decision_documented` | A separate clinician decision has been documented. | `needs_clinician_decision` | `follow_up_recommended`, `external_referral_recommended`, `closed_for_now` | Physician | Decision audit required if implemented | Finding itself is not the decision object |
| `follow_up_recommended` | Follow-up has been recommended. | `reviewed`, `decision_documented` | `closed_for_now` | Physician | Recommendation audit required if implemented | Not automatic scheduling |
| `external_referral_recommended` | External referral has been recommended. | `reviewed`, `decision_documented` | `closed_for_now` | Physician | Recommendation audit required if implemented | Not automatic referral |
| `closed_for_now` | Finding is temporarily closed with context. | `reviewed`, `decision_documented`, `follow_up_recommended`, `external_referral_recommended` | `awaiting_review` if reopened later | Physician or authorized reviewer by future policy | Closure reason required if implemented | Not permanent cure or outcome proof |

## Forbidden Or Dangerous Statuses

Do not use:

- `approved`
- `cleared`
- `resolved_by_ai`
- `diagnosed_by_ai`
- `treatment_started`
- `patient_notified`
- `task_completed`
- `outcome_proven`

## Transition Principle

Transitions must not automatically create:

- Task
- Outcome Evidence
- patient message
- appointment status mutation
- treatment plan
- diagnosis
- readiness clearance

## Runtime Boundary

D2 is documentation-only.

