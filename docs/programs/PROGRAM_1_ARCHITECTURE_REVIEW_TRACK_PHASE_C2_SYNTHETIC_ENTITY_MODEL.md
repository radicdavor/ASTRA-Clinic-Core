# Program 1 Architecture Review Track Phase C2 - Synthetic Entity Model

Status: documentation-only, synthetic-only entity model.

## Synthetic entity register

| Synthetic entity | Purpose | Allowed current use | Prohibited current use | Real patient data? | PHI/PII? | Runtime action? | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SyntheticPatient | Abstract person placeholder | Text-only architecture discussion | Real patient profile, identifier, or derived patient example | No | No | No | Synthetic-only |
| SyntheticEncounter | Abstract interaction placeholder | Conceptual encounter trace | Real appointment, visit, or care episode | No | No | No | Synthetic-only |
| SyntheticFinding | Abstract finding placeholder | Conceptual finding trace | Real clinical finding | No | No | No | Synthetic-only |
| SyntheticRecommendationPlaceholder | Abstract recommendation placeholder | Conceptual review output discussion | Patient instruction or treatment execution | No | No | No | Synthetic-only |
| SyntheticClinicianReviewPlaceholder | Abstract human review placeholder | Conceptual human-in-the-loop trace | Clinical validation, deployment, or autonomous review | No | No | No | Synthetic-only |
| SyntheticAppointmentPlaceholder | Abstract scheduling placeholder | Prohibition discussion only | Appointment creation, cancellation, reschedule, or status change | No | No | No | Synthetic-only |
| SyntheticMessagePlaceholder | Abstract communication placeholder | Prohibition discussion only | Patient message, reminder, portal output, or staff-mediated communication | No | No | No | Synthetic-only |
| SyntheticAuditConcept | Abstract audit concept | Deferred audit discussion only | Runtime audit event capture or storage | No | No | No | Synthetic-only |
| SyntheticAuthorizationConcept | Abstract authorization concept | Deferred authorization discussion only | Runtime access grant, RBAC, or policy enforcement | No | No | No | Synthetic-only |
| SyntheticOutcomePlaceholder | Abstract outcome placeholder | Prohibition discussion only | Outcome Evidence creation | No | No | No | Synthetic-only |

## Decision

Every entity is synthetic-only. No entity may represent, derive from, contain, trigger, or be connected to real patient data, PHI/PII, runtime action, production data flow, read-only runtime access, write-back behavior, patient communication, appointment mutation, workflow enforcement, audit capture, RBAC enforcement, or approval/override capability.
