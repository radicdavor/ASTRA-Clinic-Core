# Program 1 Phase G0 - Timeline Read API Prototype Design

Phase G implements one patient-scoped GET-only Clinical Evidence Timeline prototype.

Implemented route scope:

- `GET /api/patients/{patient_id}/clinical-evidence-timeline`
- patient-scoped list only
- no detail endpoint
- no POST, PATCH, PUT or DELETE

Aggregation sources:

- `ClinicalFinding`
- `ClinicalOpenQuestion`
- `ClinicalReadinessSnapshot`
- `ClinicalReadinessReviewAcknowledgment`

The endpoint maps existing read-only/source-linked objects into passive timeline event previews. It does not persist timeline events and does not create new clinical truth.

Permission/auth:

- authenticated user required
- `clinical_evidence_timeline.read` required
- API key access denied by runtime boundary
- no write, review, approval, clearance or override permission

Filtering:

- `event_type`
- `source_type`
- `requires_review`
- `date_from`
- `date_to`

Response boundary:

- source-linked event preview shape
- provenance and limitations required
- no diagnosis, treatment, Task, Outcome Evidence, patient message, approval, clearance or override fields

Production/real-data status:

- demo/pilot only
- no production approval
- no real patient data approval

