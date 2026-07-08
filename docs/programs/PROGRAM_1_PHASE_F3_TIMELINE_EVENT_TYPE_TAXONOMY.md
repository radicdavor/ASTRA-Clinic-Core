# Program 1 Phase F3 - Timeline Event Type Taxonomy

Status: documented

| Event Type | Definition | Source Object | Display Label | Forbidden Interpretation |
| --- | --- | --- | --- | --- |
| `clinical_document_received` | Document exists in patient context. | ClinicalDocument | Document received | Reviewed or approved |
| `clinical_document_review_pending` | Document needs human review. | ClinicalDocument | Review pending | Diagnosis |
| `finding_recorded` | Finding was recorded. | ClinicalFinding | Finding recorded | Diagnosis confirmed |
| `finding_requires_review` | Finding needs review. | ClinicalFinding | Finding requires review | Task created |
| `open_question_suggested` | Question suggested from source context. | ClinicalOpenQuestion | Open question suggested | Decision made |
| `open_question_awaiting_review` | Question awaits review. | ClinicalOpenQuestion | Awaiting review | Resolved |
| `extraction_candidate_generated` | Passive candidate exists. | ClinicalFindingExtractionCandidate | Extraction candidate | Official truth |
| `review_pending` | Review is pending. | ClinicalReviewPreview | Review pending | Approval pending |
| `review_completed` | Human review occurred. | ClinicalReviewPreview | Reviewed | Approved/cleared |
| `readiness_snapshot_captured` | Snapshot captured. | ClinicalReadinessSnapshot | Snapshot captured | Workflow enforcement |
| `readiness_snapshot_superseded` | Snapshot superseded additively. | ClinicalReadinessSnapshot | Snapshot superseded | Old payload changed |
| `acknowledgment_recorded` | Human acknowledged advisory context. | ClinicalReadinessReviewAcknowledgment | Acknowledgment recorded | Clearance |
| `access_audit_recorded` | Access/security audit exists. | Audit event | Access audit | Outcome Evidence |

## Forbidden Event Types

`diagnosis_confirmed_by_ai`, `treatment_started_automatically`, `patient_notified_automatically`, `task_completed`, `outcome_proven`, `procedure_approved`, `patient_cleared`, `override_applied`.
