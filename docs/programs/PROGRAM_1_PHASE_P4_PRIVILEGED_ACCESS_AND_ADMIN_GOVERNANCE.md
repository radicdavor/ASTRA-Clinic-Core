# Program 1 Phase P4 - Privileged Access and Admin Governance

No privileged access workflow is implemented by Phase P.

| Control Name | Purpose | Risk Addressed | Owner Type | Required Future Evidence | Required Future Validation | Current Status | Explicit Prohibition Still Active |
| --- | --- | --- | --- | --- | --- | --- | --- |
| admin account issuance | control who becomes admin | uncontrolled privilege | Security/operations owner | admin issuance policy | account creation tests | design only | no production admin approval |
| least-privilege admin roles | reduce admin scope | excessive access | Security owner | admin role matrix | negative permission tests | design only | no broad admin access |
| privileged access approval requirement | require review before privilege | unreviewed access | Security/compliance owner | approval procedure | access request simulation | design only | no approval workflow implemented |
| time-limited privileged access | limit duration | stale privilege | Security/operations owner | expiration policy | expiry tests | design only | no time-limited runtime |
| support access governance | control support users | support data exposure | Operations/security owner | support access policy | support access audit | design only | no support PHI access |
| break-glass access design | emergency access concept | unsafe emergency access | Clinical/security/legal owners | break-glass policy | tabletop drill | design only | no break-glass runtime |
| admin action auditability | trace admin actions | invisible privilege use | Security/compliance owner | admin audit model | admin audit tests | design only | no admin audit implementation |
| secrets access governance | restrict secrets | credential leakage | Security/operations owner | secrets access policy | rotation/access tests | design only | no production secrets claim |
| database access governance | restrict direct DB access | data bypass | Engineering/security owner | DB access policy | DB audit/access tests | design only | no real-data DB access |
| production environment access governance | govern production access | production misuse | Operations/security owner | production access design | production access review | design only | no production authorization |
| access revocation | remove privilege quickly | lingering access | Operations/security owner | revocation procedure | revocation timing test | design only | no revocation control implemented |
| periodic admin access review | recertify privilege | privilege drift | Security/compliance owner | review schedule | sample review | design only | no access review completed |
| privileged action monitoring | detect risky actions | undetected misuse | Security owner | monitoring design | alert simulation | design only | no monitoring implementation |
