# Program 1 Architecture Review Track Phase C4 - Allowed Synthetic Trace Paths

Status: documentation-only, synthetic-only trace register.

| Source | Target | Allowed current interpretation | Prohibited interpretation | Runtime status | Data boundary | Current decision |
| --- | --- | --- | --- | --- | --- | --- |
| SyntheticPatient | SyntheticEncounter | Synthetic conceptual relationship | Real patient visit flow | None | Synthetic only | Allowed as documentation trace only |
| SyntheticEncounter | SyntheticFinding | Synthetic conceptual finding relationship | Real clinical finding extraction | None | Synthetic only | Allowed as documentation trace only |
| SyntheticFinding | SyntheticClinicianReviewPlaceholder | Synthetic review concept | Clinical deployment or validation | None | Synthetic only | Allowed as documentation trace only |
| SyntheticClinicianReviewPlaceholder | SyntheticRecommendationPlaceholder | Human review concept | Treatment execution or patient instruction | None | Synthetic only | Allowed as documentation trace only |
| SyntheticAppointmentPlaceholder | Architecture review discussion only | Prohibited scheduling discussion | Appointment mutation | None | Synthetic only | Allowed as prohibition trace only |
| SyntheticMessagePlaceholder | Prohibited communication discussion only | Prohibited communication discussion | Patient messaging | None | Synthetic only | Allowed as prohibition trace only |
| SyntheticAuditConcept | Deferred audit discussion only | Audit architecture concept | Runtime audit capture | None | Synthetic only | Allowed as deferred concept only |
| SyntheticAuthorizationConcept | Deferred authorization discussion only | Authorization architecture concept | Runtime RBAC or access grant | None | Synthetic only | Allowed as deferred concept only |

## Decision

Allowed synthetic trace paths remain documentation-only and synthetic-only. They do not create runtime data flow, real-data ingestion, PHI/PII processing, read-only runtime access, write-back behavior, patient messaging, appointment mutation, workflow enforcement, audit capture, RBAC enforcement, approval/clearance/override capability, production use, or go-live authorization.
