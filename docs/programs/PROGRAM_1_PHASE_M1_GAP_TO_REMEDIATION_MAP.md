# Program 1 Phase M1 - Gap to Remediation Map

| Gap Category | Remediation Objective | Future Workstream | Required Owner Type | Required Evidence | Dependencies | Risk If Unresolved | Can Be Closed In Phase M? | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical safety gaps | define safety controls and responsibility | governance control design | Clinical owner | safety model and sign-off criteria | Phase L gap review | unsafe interpretation | No | planning only |
| Real patient data governance gaps | define real-data legal/privacy controls | real-data governance design | Legal/compliance owner | GDPR/DPIA and data policy | legal review | unlawful data use | No | no real-data approval |
| Human responsibility gaps | define accountable roles | responsibility model | Clinical owner | responsibility matrix | governance controls | unclear authority | No | no owner sign-off |
| Access control and identity gaps | define least-privilege access | RBAC/access design | Security/privacy owner | access matrix and tests | identity policy | overbroad access | No | no implementation |
| Auditability and traceability gaps | define audit completeness | auditability design | Compliance owner | audit coverage evidence | access model | weak accountability | No | no validation package |
| Validation and regression coverage gaps | define production validation package | validation plan | QA/validation owner | test matrix and evidence archive | safety model | false confidence | No | no production validation |
| Operational readiness gaps | define runbooks and support | operations plan | Operations owner | support/runbook evidence | deployment model | fragile operations | No | no ops approval |
| Monitoring and incident response gaps | define alerts and response | monitoring/incident plan | Operations owner | alert and incident drill evidence | deployment model | delayed response | No | no monitoring setup |
| Rollback and disaster recovery gaps | define restore/rollback proof | DR plan | Operations owner | restore drill record | backup model | data loss/outage | No | no drill performed |
| Training and operator readiness gaps | define role training | training plan | Product owner | training materials and sign-off | usability review | misuse | No | no training approval |
| Legal/compliance/privacy gaps | define compliance path | legal review plan | Legal/compliance owner | formal review artifacts | data governance | unlawful claims/use | No | no review complete |
| Deployment/environment hardening gaps | define hardened environment | deployment hardening | Engineering owner | hardened checklist | security policy | insecure runtime | No | no deployment change |
| Data lifecycle and retention gaps | define lifecycle policy | data governance | Data governance owner | retention/export/delete policy | legal basis | improper retention | No | no policy approval |
| Patient communication safety gaps | define prohibition or future controls | communication safety | Clinical/legal owner | future design if proposed | governance controls | unsafe messaging | No | remains no-go |
| Appointment/workflow mutation safety gaps | define prohibition or future controls | workflow mutation safety | Product/clinical owner | future design if proposed | safety model | unintended workflow changes | No | remains no-go |
| Clinical write-workflow safety gaps | define prohibition or approval path | write workflow safety | Clinical/product/legal owners | separate design and approval package | all governance controls | unsafe clinical state changes | No | remains no-go |
