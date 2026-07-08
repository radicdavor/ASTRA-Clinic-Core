# Program 1 Phase P2 - Least-Privilege and Access Boundary Model

Phase P documents future least-privilege boundaries only. No runtime access-control behavior is added.

| Resource/Action Category | Future Access Boundary | Read Access Consideration | Write/Mutate Access Consideration | Privileged Access Consideration | Audit Requirement | Owner Type | Evidence Required Before Future Implementation | Current Decision | Explicit Prohibition Still Active |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| patient/person records | patient-scoped, role-limited | requires real-data approval first | not approved | admin access restricted | view/search audit | Data/security owner | RBAC matrix and tests | not approved | no real-data access |
| clinical readiness snapshots | source-linked clinical read surface | role-scoped read | no new mutation from Phase P | privileged review only | access and mutation audit | Clinical/security owner | permission design | design only | no new write behavior |
| acknowledgments/advisories | advisory read/write boundaries | role-scoped read | existing behavior not expanded | privileged audit review | access/action audit | Clinical/product owner | boundary tests | design only | no workflow enforcement |
| findings | clinical finding read surface | role-scoped read | write workflows not approved | privileged access reviewed | view/search audit | Clinical/security owner | access tests | design only | no clinical write workflow |
| open questions | source-linked open question read | role-scoped read | write/review not approved | privileged access reviewed | view/search audit | Clinical/product owner | access tests | design only | no review/write endpoint |
| extraction records | extraction-related records | role-scoped read if future approved | runtime AI/OCR not approved | privileged access restricted | access audit | Product/security owner | access and safety tests | design only | no real AI/OCR |
| evidence timeline | read-only aggregation | patient-scoped read | no write behavior | privileged access restricted | timeline access audit candidate | Product/security owner | traceability tests | design only | no timeline write |
| review workflow metadata | future review metadata | role-scoped read | review runtime not approved | privileged access restricted | review access audit | Clinical/security owner | review control design | not approved | no review endpoint |
| demo documentation | public/internal docs | broad demo access | documentation edits controlled | repo admin controlled | git history | Product owner | doc review | allowed as docs | no production claim |
| configuration | system configuration | limited admin read | controlled change only | admin-only | config change audit | Engineering/security owner | config policy | design only | no production config claim |
| audit logs | accountability records | restricted auditor/security read | append-only if future implemented | highly restricted | audit log access audit | Security/compliance owner | audit policy | not implemented | no audit enforcement |
| attachments/documents | sensitive documents | no real-data access | upload/change not expanded | restricted support/admin | document access audit | Security/data owner | storage control evidence | not approved | no real documents |
| user/admin settings | identity/admin settings | self/admin scoped | admin-governed changes | privileged access | settings change audit | Security/operations owner | admin policy | design only | no admin workflow approval |
| integration endpoints | external access | integration-scoped | no write without approval | key/service account governance | API access audit | Security/product owner | integration contract | design only | no integration approval |
| database/admin operations | data-layer operations | restricted operations | production mutation not approved | DB admin only | privileged operation audit | Engineering/security owner | DB access policy | not approved | no real-data DB access |
| export operations | data extraction | restricted | not approved | privileged and legal-gated | export attempt audit | Legal/data owner | export procedure | not approved | no export approval |
| deletion operations | data deletion | restricted | not approved | privileged and legal-gated | deletion attempt audit | Legal/data owner | deletion procedure | not approved | no deletion workflow |
| patient messaging | communication | not approved | not approved | not allowed | messaging attempt audit if future exists | Product/legal owner | messaging governance | prohibited | no patient messaging |
| appointment status mutation | workflow mutation | not approved | not approved | not allowed | mutation attempt audit if future exists | Product/operations owner | workflow governance | prohibited | no appointment mutation |
| clinical write workflows | clinical state mutation | not approved | not approved | not allowed | clinical write attempt audit | Clinical/product owner | clinical safety package | prohibited | no clinical write workflow |
| approval/clearance/override actions | high-risk decisions | not approved | not approved | not allowed | attempt audit if future exists | Clinical/legal owner | gate design and validation | prohibited | no approval/clearance/override |
| Task engine actions | task workflow | not approved | not approved | not allowed | task attempt audit if future exists | Product owner | task governance | prohibited | no Task engine |
| Outcome Evidence actions | outcome claims | not approved | not approved | not allowed | outcome attempt audit if future exists | Clinical/legal owner | evidence governance | prohibited | no Outcome Evidence |
