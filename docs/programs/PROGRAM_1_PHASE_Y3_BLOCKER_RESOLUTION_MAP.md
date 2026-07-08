# Program 1 Phase Y3 - Blocker Resolution Map

| Unresolved blocker | Required review | Required artifact | Allowed current action | Prohibited current action | Future dependency | Current decision |
| --- | --- | --- | --- | --- | --- | --- |
| production approval | governance/product/operations | production approval path | document gap | claim production readiness | authorized future phase | blocked |
| real-data approval | privacy/legal/data governance | real-data governance approval | document gap | ingest real data | legal/privacy approval | blocked |
| PHI/PII processing | privacy/legal/security | PHI/PII processing model | document gap | process PHI/PII | security/privacy review | blocked |
| clinical safety | clinical owner | clinical safety model | document gap | automate diagnosis/treatment | clinical review | blocked |
| clinical accountability | clinical/product/legal | accountability model | document gap | deploy clinically | owner sign-off | blocked |
| runtime authorization | security/engineering | auth/RBAC design | document design need | implement runtime auth | security architecture | deferred |
| runtime auditability | security/engineering/QA | audit model | document design need | implement audit logging | audit validation plan | deferred |
| patient communication | clinical/legal/product | messaging safety model | document no-go | add messaging | separate approval | prohibited |
| appointment mutation | clinical/operations/product | appointment mutation model | document no-go | mutate appointments | separate approval | prohibited |
| workflow enforcement | clinical/product/engineering | workflow safety design | document no-go | enforce workflow | separate approval | prohibited |
| clinical write path | clinical/product/engineering | write-path governance | document no-go | add write workflows | separate approval | prohibited |
| validation evidence | QA/validation | validation evidence package | document evidence need | claim validated status | implemented tests and review | blocked |
| deployment governance | operations/security | deployment governance model | document gap | deploy live | operations approval | blocked |
| rollback/incident response | operations/security | incident/rollback model | document gap | authorize go-live | drills and evidence | blocked |
| documentation consistency | product/engineering | consistency review | update docs | imply maturity | future review | clarify only |
