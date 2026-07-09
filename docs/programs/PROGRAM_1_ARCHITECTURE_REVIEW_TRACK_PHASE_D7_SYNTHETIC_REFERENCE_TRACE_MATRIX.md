# Program 1 Architecture Review Track Phase D7 - Synthetic Reference Trace Matrix

Status: documentation-only, synthetic-only reference matrix.

| Reference concept | Allowed in Phase D | Prohibited in Phase D | Data class allowed | Runtime status | Mutation status | Future dependency | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Synthetic patient reference | Text-only reference | Real patient record viewing | Synthetic only | None | None | Future authorization for any expansion | Allowed as docs only |
| Synthetic encounter reference | Text-only reference | Real encounter access | Synthetic only | None | None | Future authorization for any expansion | Allowed as docs only |
| Synthetic finding reference | Text-only reference | Real clinical finding access | Synthetic only | None | None | Future authorization for any expansion | Allowed as docs only |
| Synthetic appointment reference | Prohibition discussion | Appointment system access or mutation | Synthetic only | None | Prohibited | Appointment governance review | Allowed as docs only |
| Synthetic message reference | Prohibition discussion | Patient message access or sending | Synthetic only | None | Prohibited | Patient communication governance | Allowed as docs only |
| Synthetic clinician review reference | Human review concept | Clinical deployment or validation | Synthetic only | None | None | Clinical safety review | Deferred |
| Synthetic audit concept | Deferred concept | Audit capture or audit log inspection | Synthetic only | Not implemented | Prohibited | Audit/security review | Deferred |
| Synthetic authorization concept | Deferred concept | Runtime auth/authz/RBAC | Synthetic only | Not implemented | Prohibited | Security architecture review | Deferred |
| Future read-only reference concept | Conceptual discussion | Runtime read-only access | Synthetic only | Not implemented | None | Read-only authorization and validation | Deferred |
| Operational read access | Not allowed | Real system or record connection | None | Prohibited | None | Explicit future authorization | Prohibited |
| Write-capable operation | Not allowed | Any mutation/writeback | None | Prohibited | Prohibited | Separate future authorization | Prohibited |
| Production deployment concept | Boundary discussion only | Deployment automation or go-live | None | Prohibited | Prohibited | Production governance review | Prohibited |

## Decision

The matrix is documentation-only. It does not authorize read-only runtime access, operational access, write-back behavior, mutation behavior, production use, real-data use, PHI/PII processing, clinical deployment, or go-live.
