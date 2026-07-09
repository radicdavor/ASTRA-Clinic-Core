# Program 1 Architecture Review Track Phase B7 - Prohibited Coupling Map

Status: documentation-only prohibited coupling register.

## Prohibited couplings

| Source concept | Prohibited target | Why prohibited | Current decision | Required future authorization before reconsideration |
| --- | --- | --- | --- | --- |
| Synthetic documentation layer | Real patient data | Would violate synthetic-only review | Prohibited | Real-data governance, privacy/legal, security, and explicit hold-exit authorization |
| Architecture review layer | Runtime code | Would convert review into implementation | Prohibited | Explicit future implementation authorization |
| Future read-only layer | Write-capable operations | Would create mutation and clinical workflow risk | Prohibited | Governance, clinical safety, validation, and implementation authorization |
| Clinical review layer | Autonomous diagnosis | Would create autonomous clinical behavior | Prohibited | Clinical safety and accountability authorization |
| Clinical review layer | Autonomous treatment | Would create autonomous clinical behavior | Prohibited | Clinical safety and accountability authorization |
| Read-only layer | Patient messaging | Would create patient communication path | Prohibited | Patient communication governance and explicit implementation authorization |
| Read-only layer | Appointment mutation | Would create scheduling mutation path | Prohibited | Scheduling governance and explicit implementation authorization |
| Audit concept | Runtime audit capture | Would create runtime audit behavior | Prohibited | Audit/security architecture and implementation authorization |
| Authorization concept | Runtime RBAC enforcement | Would create runtime authorization behavior | Prohibited | Security architecture and implementation authorization |
| Blocker map | Approval/override capability | Would imply clearance or override execution | Prohibited | Separate governance authorization; no automatic approval |
| Documentation state | Production-readiness claim | Would overstate maturity | Prohibited | Formal production governance review and explicit authorization |
| Roadmap entry | Go-live authorization | Would confuse planning with deployment | Prohibited | Separate future go-live decision |

## Current decision

No prohibited coupling is accepted by Phase B. All prohibited targets remain deferred, not implemented, not approved, and not authorized.
