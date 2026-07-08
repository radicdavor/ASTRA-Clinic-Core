# Program 1 Phase G Module Inventory

Runtime added:

- GET-only patient-scoped timeline read API
- side-effect-free aggregation helper
- read-only permission `clinical_evidence_timeline.read`
- targeted timeline read API tests

Schemas used:

- `ClinicalEvidenceTimelineSourceReference`
- `ClinicalEvidenceTimelineEventPreview`
- `ClinicalEvidenceTimelineListResponse`

Aggregated objects:

- `ClinicalFinding`
- `ClinicalOpenQuestion`
- `ClinicalReadinessSnapshot`
- `ClinicalReadinessReviewAcknowledgment`

No-go surfaces:

- no POST/PATCH/PUT/DELETE timeline endpoint
- no timeline DB model/migration
- no frontend timeline UI/client
- no Task engine
- no Outcome Evidence
- no patient messaging
- no automatic diagnosis/treatment
- no approval/clearance/override

Production/real-data status: No-Go.

