# Program 1 Architecture Review Track Phase F8 - Conceptual Control Matrix

Status: documentation-only conceptual control matrix.

| Control concept | Allowed in Phase F | Prohibited in Phase F | Runtime status | Data status | Enforcement status | Future dependency | Current decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Security principle | Conceptual discussion | Runtime control | None | Synthetic only | None | Security review | Allowed as docs only |
| Trust boundary concept | Conceptual discussion | Network or system control | None | Synthetic only | None | Security architecture review | Allowed as docs only |
| Least privilege concept | Conceptual discussion | Access enforcement | None | Synthetic only | None | Authorization review | Deferred |
| Future role taxonomy | Conceptual discussion | User/role implementation | Not implemented | Synthetic only | None | Security/governance review | Deferred |
| Future permission taxonomy | Conceptual discussion | Permission enforcement | Not implemented | Synthetic only | None | Security/governance review | Deferred |
| Authentication concept | Conceptual discussion | Runtime authentication | Not implemented | Synthetic only | None | Security review | Deferred |
| Authorization concept | Conceptual discussion | Runtime authorization | Not implemented | Synthetic only | None | Security review | Deferred |
| RBAC concept | Conceptual discussion | RBAC enforcement | Not implemented | Synthetic only | None | Security/governance review | Deferred |
| Audit event concept | Conceptual discussion | Audit capture/storage | Not implemented | Synthetic only | None | Audit/security review | Deferred |
| Access log concept | Conceptual discussion | Access log capture | Not implemented | Synthetic only | None | Audit/security review | Deferred |
| Incident response concept | Conceptual discussion | Incident automation | Not implemented | Synthetic only | None | Operational review | Deferred |
| Rollback concept | Conceptual discussion | Rollback execution | Not implemented | Synthetic only | None | Operational review | Deferred |
| Approval concept | Future dependency mention | Approval gate | Prohibited | Synthetic only | Prohibited | Governance authorization | Prohibited |
| Clearance concept | Future dependency mention | Clearance gate | Prohibited | Synthetic only | Prohibited | Governance authorization | Prohibited |
| Override concept | Future dependency mention | Override gate | Prohibited | Synthetic only | Prohibited | Governance authorization | Prohibited |
| Policy enforcement concept | Prohibition discussion | Runtime policy enforcement | Prohibited | Synthetic only | Prohibited | Governance and security review | Prohibited |
| Production access concept | Boundary discussion | Production access | Prohibited | None | Prohibited | Production governance review | Prohibited |

## Decision

The matrix is conceptual only. It does not authorize runtime implementation, runtime security enforcement, runtime authorization/RBAC, audit capture, access logging, policy enforcement, approval/clearance/override capability, production access, real-data use, PHI/PII processing, clinical deployment, or go-live.
