# Program 1 Architecture Review Track Phase D4 - Prohibited Read Access Paths

Status: documentation-only prohibited read access register.

| Source | Prohibited target | Why prohibited | Current decision | Future review dependency before reconsideration |
| --- | --- | --- | --- | --- |
| EHR/EMR | Program 1 | Would create clinical system access | Prohibited | Real-data, security, clinical safety, and production governance review |
| Production database | Program 1 | Would create production data access | Prohibited | Production governance and security architecture review |
| Patient portal | Program 1 | Would create patient communication or portal data access | Prohibited | Patient communication, privacy/legal, and security review |
| Appointment system | Program 1 | Would create scheduling record access | Prohibited | Appointment governance and security review |
| Staff workflow system | Program 1 | Would create operational workflow access | Prohibited | Workflow governance and security review |
| Real clinical notes | Program 1 | Would create clinical data processing | Prohibited | Clinical safety, privacy/legal, and real-data review |
| Real lab/imaging/endoscopy data | Program 1 | Would create clinical data processing | Prohibited | Clinical safety, privacy/legal, and real-data review |
| Real audit logs | Program 1 | Would create audit data inspection | Prohibited | Audit/security architecture review |
| Real authorization logs | Program 1 | Would create runtime authorization data access | Prohibited | Security architecture review |
| Real patient messages | Program 1 | Would create patient communication data access | Prohibited | Patient communication and privacy/legal review |
| PHI/PII store | Program 1 | Would create PHI/PII processing | Prohibited | PHI/PII processing approval and privacy/legal review |

## Decision

No prohibited read access path is allowed by Phase D. Operational access, read-only runtime access, real-data inspection, PHI/PII processing, database queries, EHR/EMR access, patient record viewing, production data inspection, audit log inspection, authorization log inspection, and patient message inspection remain not approved, not cleared, not implemented, and not authorized.
