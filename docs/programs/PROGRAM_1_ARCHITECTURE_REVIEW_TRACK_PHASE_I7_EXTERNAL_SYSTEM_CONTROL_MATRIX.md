# Program 1 Architecture Review Track Phase I7 - External System Control Matrix

Status: documentation-only, synthetic-only external system control matrix.

| External system concept | Allowed in Phase I | Prohibited in Phase I | Runtime status | Data status | Connector status | Future dependency | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Integration concept | Documentation discussion | Runtime integration | None | Synthetic only | None | Integration governance review | Allowed as docs only |
| API concept | Boundary discussion | API client/endpoint/adapter | None | No real data | Prohibited | API/security review | Prohibited |
| Database concept | Dependency discussion | Database client/query/access | None | No production data | Prohibited | Data/security/privacy review | Prohibited |
| EHR/EMR concept | Boundary discussion | EHR/EMR connector/access | None | No PHI/PII | Prohibited | Clinical/privacy/security review | Prohibited |
| Patient portal concept | Boundary discussion | Portal connector/access | None | No patient data | Prohibited | Privacy/patient communication review | Prohibited |
| Appointment system concept | Boundary discussion | Appointment sync/mutation | None | No operational data | Prohibited | Operations/security review | Prohibited |
| Messaging concept | Boundary discussion | Patient/staff messaging | None | No message data | Prohibited | Privacy/legal review | Prohibited |
| Audit concept | Boundary discussion | Audit capture/write | None | No audit logs | Prohibited | Audit/security/privacy review | Prohibited |
| Authorization concept | Boundary discussion | RBAC enforcement | None | No identities | Prohibited | Security review | Prohibited |
| FHIR/HL7 concept | Boundary discussion | FHIR/HL7 integration | None | No real data | Prohibited | Interoperability/privacy/security review | Prohibited |

## Decision

Phase I allows only documentation discussion. Every connector, API, runtime data exchange, real-data access, PHI/PII processing path, mutation path, or external system access path remains prohibited.
