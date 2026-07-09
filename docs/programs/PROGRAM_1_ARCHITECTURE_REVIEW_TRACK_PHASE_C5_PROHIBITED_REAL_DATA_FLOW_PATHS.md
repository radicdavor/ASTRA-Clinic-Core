# Program 1 Architecture Review Track Phase C5 - Prohibited Real-Data Flow Paths

Status: documentation-only prohibited flow register.

| Source | Prohibited target | Why prohibited | Current decision | Required future authorization before reconsideration |
| --- | --- | --- | --- | --- |
| Real patient record | Any Program 1 module | Would create real-data processing | Prohibited | Real-data governance, privacy/legal, security, and explicit future authorization |
| PHI/PII | Synthetic documentation layer | Would break synthetic-only boundary | Prohibited | PHI/PII processing approval and privacy/legal review |
| Production database | Architecture review layer | Would connect review to production data | Prohibited | Production governance and security review |
| Clinic appointment system | Program 1 flow | Would create scheduling integration risk | Prohibited | Appointment governance and explicit implementation authorization |
| Patient portal | Program 1 flow | Would create patient communication path | Prohibited | Patient communication governance and explicit authorization |
| EHR/EMR | Program 1 flow | Would create clinical data integration | Prohibited | Real-data, security, clinical safety, and production governance review |
| Staff workflow system | Program 1 flow | Would create workflow enforcement or staff-mediated patient communication risk | Prohibited | Workflow governance and explicit implementation authorization |
| Real audit logs | Program 1 audit concept | Would create real audit data handling | Prohibited | Audit/security architecture and privacy review |
| Real authorization events | Program 1 authorization concept | Would create runtime access-control data handling | Prohibited | Security architecture and implementation authorization |
| Real messages | Patient messaging concept | Would create patient communication handling | Prohibited | Patient communication governance and privacy/legal review |
| Real clinical notes | Clinical review concept | Would create clinical data processing | Prohibited | Clinical safety, real-data, privacy/legal, and implementation authorization |

## Decision

No real-data flow path is allowed by Phase C. All real-data, PHI/PII, production, clinical, appointment, portal, EHR/EMR, workflow, audit, authorization, messaging, and clinical-note flows remain not approved, not cleared, not implemented, and not authorized.
