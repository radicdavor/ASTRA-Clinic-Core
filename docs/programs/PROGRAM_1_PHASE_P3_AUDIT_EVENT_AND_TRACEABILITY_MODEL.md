# Program 1 Phase P3 - Audit Event and Traceability Model

Phase P does not implement audit logging.

Phase P only designs future audit event requirements.

Minimum future fields, where relevant: timestamp, actor identity, role/context, action, resource type, resource identifier, result/success/failure, reason/context, source/IP or environment, correlation/request ID, and before/after state where applicable.

| Event Category | Why It Matters | Minimum Future Fields | Required Traceability | Retention Consideration | Access to Audit Record | Alerting Consideration | Required Validation | Current Status | Non-Implementation Statement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| login/logout | prove session activity | actor, timestamp, result, source | identity to session | security retention | security/admin | unusual pattern | auth event tests | design only | no logging added |
| failed authentication | detect abuse | actor/source, failure reason, timestamp | source to attempt | security retention | security | repeated failure | negative auth tests | design only | no logging added |
| role/permission change | track privilege changes | actor, target, before/after, reason | admin to changed account | long retention | security/compliance | privileged change | change audit tests | design only | no RBAC logging |
| record view | trace PHI access | actor, record, result, request ID | user to viewed record | privacy retention | compliance/security | sensitive access | access audit tests | design only | no view audit |
| record search | trace discovery | actor, query class, result count | user to search | privacy retention | compliance/security | broad search | search audit tests | design only | no search audit |
| clinical readiness snapshot access | trace snapshot reads | actor, patient/snapshot, result | user to snapshot | clinical audit retention | compliance/clinical | unusual access | read audit tests | design only | no new audit |
| acknowledgment/advisory access | trace advisory reads | actor, resource, result | user to advisory | clinical audit retention | compliance/clinical | denied access | read audit tests | design only | no new audit |
| finding/open question access | trace clinical reads | actor, patient/resource, result | user to finding/question | privacy retention | compliance/clinical | sensitive access | source-link trace tests | design only | no new audit |
| extraction record access | trace generated candidate access | actor, resource, result | user to extraction record | clinical/privacy retention | compliance/security | unusual access | access tests | design only | no logging added |
| timeline access | trace aggregate reads | actor, patient, filters, result | user to timeline query | privacy retention | compliance/security | broad access | query audit tests | design only | no timeline audit |
| review workflow access | trace future review reads | actor, review object, result | user to review object | clinical retention | clinical/compliance | denied access | review audit tests | design only | no review audit |
| configuration change | track system changes | actor, key, before/after, reason | admin to config | operations retention | security/ops | high-risk change | config audit tests | design only | no config audit |
| export attempt | detect data exfiltration | actor, scope, result, reason | user to export scope | long retention | security/legal | any export | export negative tests | design only | no export workflow |
| deletion attempt | trace lifecycle changes | actor, resource, result, reason | user to deletion target | legal retention | legal/security | deletion attempt | deletion audit tests | design only | no deletion workflow |
| attachment/document access | trace document reads | actor, document, result | user to document | privacy retention | compliance/security | sensitive doc access | document audit tests | design only | no doc audit |
| admin action | trace privileged work | actor, action, target, result | admin to action | long retention | security/ops | privileged action | admin audit tests | design only | no admin workflow |
| integration/API access | trace API actors | actor/key, endpoint, result | integration to request | security retention | security | failed/broad access | API audit tests | design only | no integration audit |
| security event | detect threats | event, source, severity, result | event to context | security retention | security | severity-based | alert tests | design only | no event pipeline |
| privacy-sensitive access | detect high-risk access | actor, resource, reason, result | user to PHI scope | privacy retention | privacy/security | sensitive access | privacy audit tests | design only | no PHI access |
| break-glass access | govern emergency access | actor, reason, approval context, result | actor to emergency context | long retention | clinical/security/legal | all events | tabletop and audit tests | design only | no break-glass workflow |
| patient messaging attempt | prevent unauthorized contact | actor, patient, result, reason | actor to message attempt | legal retention | legal/product | any attempt | negative tests | design only | no patient messaging |
| appointment mutation attempt | prevent workflow mutation | actor, appointment, before/after, result | actor to appointment | operations retention | operations/security | any attempt | mutation negative tests | design only | no appointment mutation |
| clinical write attempt | prevent unsafe writes | actor, resource, before/after, result | actor to clinical object | clinical retention | clinical/compliance | any attempt | write negative tests | design only | no clinical write |
| approval/clearance/override attempt | prevent false approval | actor, target, result, reason | actor to decision attempt | long retention | clinical/legal | any attempt | no-go tests | design only | no approval workflow |
| Task engine attempt | prevent task semantics | actor, target, result | actor to attempted task | product retention | product/security | any attempt | no-go tests | design only | no Task engine |
| Outcome Evidence attempt | prevent outcome claims | actor, target, result | actor to attempted outcome | clinical/legal retention | clinical/legal | any attempt | no-go tests | design only | no Outcome Evidence |
