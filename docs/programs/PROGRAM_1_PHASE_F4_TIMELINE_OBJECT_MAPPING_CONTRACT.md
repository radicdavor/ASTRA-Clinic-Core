# Program 1 Phase F4 - Timeline Object Mapping Contract

Status: documented

| Source Object | Event Type | Required Fields | Optional Fields | No-Go Interpretation |
| --- | --- | --- | --- | --- |
| ClinicalDocument | `clinical_document_received` | patient id, document id, source label, timestamp | document type | reviewed/approved |
| ClinicalFinding | `finding_recorded` or `finding_requires_review` | patient id, finding id, source reference, status | category | diagnosis/treatment |
| ClinicalOpenQuestion | `open_question_suggested` or `open_question_awaiting_review` | patient id, question id, source reference, status | finding id | decision/resolution |
| ClinicalFindingExtractionCandidate | `extraction_candidate_generated` | source reference, candidate key, timestamp | confidence | official truth |
| ClinicalReviewPreview | `review_pending` or `review_completed` | reviewed object reference, source reference, status | limitations | approval/clearance |
| ClinicalReadinessSnapshot | `readiness_snapshot_captured` or `readiness_snapshot_superseded` | appointment id, patient id, snapshot id | snapshot state | workflow enforcement |
| ClinicalReadinessReviewAcknowledgment | `acknowledgment_recorded` | acknowledgment id/key, patient id, appointment id | actor role | clearance/override |
| Denied-read audit event | `access_audit_recorded` or security-only event | actor/category/timestamp | request id | clinical evidence |

## Exclusions

Do not place Task completion, Outcome Evidence, patient messages, approvals, clearances, overrides or automatic AI decisions in the clinical timeline in this phase.
