# Program 1 Architecture Review Track Phase I6 - External System Dependency Map

Status: documentation-only, synthetic-only external system dependency map.

| System area | Current Phase I status | Unresolved dependency | Prohibited current action | Required future review | Current decision |
| --- | --- | --- | --- | --- | --- |
| EHR/EMR | Conceptual only | EHR governance, privacy, security, clinical accountability | Connect, query, read, write, or sync EHR/EMR | Privacy/security/clinical governance review | Prohibited |
| Production database | Not approved | Production data governance | Query or access production DB | Data/security/privacy review | Prohibited |
| Patient portal | Conceptual only | Portal access governance | Access portal or patient account data | Privacy/security/patient communication review | Prohibited |
| Appointment system | Conceptual only | Appointment integration governance | Sync or mutate appointments | Operations/security/privacy review | Prohibited |
| Messaging system | Conceptual only | Messaging governance | Send/read messages | Privacy/legal/patient communication review | Prohibited |
| Staff workflow system | Conceptual only | Workflow ownership model | Enforce workflow or create tasks | Operations/clinical governance review | Prohibited |
| Audit system | Conceptual only | Runtime audit model | Capture or write audit events | Security/audit/privacy review | Prohibited |
| Authorization system | Conceptual only | Runtime authz model | Enforce RBAC or permissions | Security review | Prohibited |
| Identity provider | Conceptual only | Identity governance | Integrate SSO/IdP | Security/privacy review | Prohibited |
| File storage | Conceptual only | File governance and retention | Ingest files or store PHI/PII | Privacy/security/retention review | Prohibited |
| Analytics/reporting system | Conceptual only | Analytics governance | Export or analyze real data | Privacy/data governance review | Prohibited |
| External API | Conceptual only | API governance and contracts | Add API client or adapter | API/security/privacy review | Prohibited |
| Integration middleware | Conceptual only | Middleware ownership and security | Add middleware/queues/jobs | Architecture/security review | Prohibited |
| FHIR/HL7 interface | Conceptual only | Interoperability governance | Add FHIR/HL7 integration | Clinical/security/privacy/interoperability review | Prohibited |

## Decision

No dependency is resolved by Phase I. No connector, integration, API, database access, EHR/EMR access, patient portal access, appointment system access, messaging system access, external system access, or runtime data exchange is approved.
