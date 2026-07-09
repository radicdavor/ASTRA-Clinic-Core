# Program 1 Architecture Review Track Phase B2 - Conceptual Module Separation Model

Status: documentation-only, synthetic-only conceptual module model.

## Module model

| Conceptual module | Purpose | Allowed current artifacts | Prohibited artifacts | Runtime status | Data boundary | Future authorization dependency |
| --- | --- | --- | --- | --- | --- | --- |
| Synthetic documentation layer | Hold architecture review in documentation | Markdown, text diagrams, abstract placeholders | Runtime code, PHI/PII, live data | None | Synthetic only | Required for any move beyond docs |
| Architecture review layer | Discuss conceptual architecture separation | Boundary docs, coupling maps | Executable design, APIs, services | None | Synthetic only | Explicit implementation authorization |
| Future read-only reference layer | Future concept for non-mutating reference | Text-only concept notes | Runtime read access | Not implemented | No real data | Future authorization and validation |
| Future clinical review layer | Future human review concept | Responsibility concept docs | Clinical deployment, autonomous action | Not implemented | No patient data | Clinical safety and accountability review |
| Prohibited write-capable layer | Identify mutation paths to block | Prohibition docs | Write services, endpoints, migrations | Prohibited | Not applicable | Separate future authorization |
| Prohibited patient communication layer | Identify communication paths to block | Prohibition docs | Messages, reminders, portal output | Prohibited | Not applicable | Separate future authorization |
| Prohibited appointment mutation layer | Identify scheduling mutation paths to block | Prohibition docs | Scheduling writes, status changes | Prohibited | Not applicable | Separate future authorization |
| Prohibited workflow enforcement layer | Identify workflow enforcement paths to block | Prohibition docs | Enforcement engines, task runners | Prohibited | Not applicable | Separate future authorization |
| Prohibited approval/clearance/override layer | Prevent approval semantics from becoming capability | Prohibition docs | Approval, clearance, override workflows | Prohibited | Not applicable | Separate future authorization |
| Deferred security/audit/authorization layer | Reserve security, audit, auth concepts for later review | Concept docs | Runtime RBAC, audit capture, policy enforcement | Not implemented | No production data | Security architecture review |

## Current decision

Only the synthetic documentation layer is currently allowed. Every runtime-capable, real-data-capable, write-capable, communication-capable, appointment-capable, workflow-capable, audit/auth-capable, or approval/override-capable module remains not approved, not cleared, not implemented, and not authorized.
