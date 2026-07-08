# Program 1 Phase N3 - Access Audit and Accountability Controls

Designing access/audit controls does not mean those controls are implemented or validated.

| Control Name | Purpose | Decision Governed | Owner Type | Required Evidence Before Closure | Required Future Validation | Prohibited Until Closure | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| User identity model | ensure named users | identity assurance | Security owner | identity policy | login/access tests | shared production accounts | no production identity approval |
| Role-based access control | restrict by role | role permissions | Security/product owners | RBAC matrix | permission tests | broad access | no access expansion approval |
| Least privilege access | minimize permissions | permission grants | Security owner | least-privilege review | negative access tests | overbroad roles | no least-privilege closure |
| Admin access governance | control admin power | admin operations | Security/operations owners | admin policy | admin audit tests | unreviewed admin access | no admin approval |
| Access review cadence | ensure periodic review | access recertification | Security/privacy owner | cadence policy | review records | unattended access drift | no cadence active |
| Audit trail completeness | prove traceability | audit coverage | Compliance owner | audit inventory | audit completeness tests | production audit claims | no completeness approval |
| Audit immutability expectations | protect audit integrity | tamper resistance | Engineering/compliance owners | immutability design | tamper tests | audit reliance | no immutability approval |
| User-action traceability | link actors to records | accountability | Compliance/security owners | traceability design | trace tests | unaudited clinical context | no traceability closure |
| Security event logging | log security events | security visibility | Security owner | logging policy | alert tests | production monitoring claims | no security logging approval |
| Privileged action monitoring | monitor sensitive actions | privileged operations | Security owner | monitoring design | privileged action tests | unmonitored privileged use | no monitoring approval |
| Operator accountability | define operator duties | operator actions | Operations owner | operator runbook | runbook exercise | unmanaged operations | no operations approval |
