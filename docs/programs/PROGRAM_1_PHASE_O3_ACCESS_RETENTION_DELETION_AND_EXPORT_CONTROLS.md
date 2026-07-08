# Program 1 Phase O3 - Access, Retention, Deletion, and Export Controls

Phase O designs lifecycle and access controls only. It does not implement these controls.

| Control Name | Purpose | Decision Governed | Required Owner Type | Required Evidence Before Closure | Required Future Validation | Prohibited Until Closure | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| role-based access control | restrict data by role | who may access real data | Security/product owner | RBAC matrix | permission tests | real-data access | no access approval |
| least privilege | minimize privileges | access scope | Security owner | least-privilege review | negative access tests | broad access | no privilege expansion |
| admin access restrictions | govern elevated access | admin visibility/actions | Security/operations owner | admin policy | privileged access test | admin real-data access | no admin approval |
| clinical user access boundaries | define clinical role access | clinical read/write scope | Clinical/security owner | role boundary document | role tests | clinical real-data access | no clinical access approval |
| operator access boundaries | restrict operators | support/admin access | Operations/security owner | support access policy | operator access test | operator real-data access | no support approval |
| break-glass policy design | define emergency access | emergency access | Security/clinical/legal owners | break-glass policy | tabletop drill | emergency access use | no break-glass approval |
| access review cadence | review access regularly | access recertification | Security/operations owner | review schedule | sample review | ongoing access | no cadence approved |
| access revocation | remove access promptly | offboarding/revocation | Operations/security owner | revocation procedure | revocation test | stale access | no revocation approval |
| audit logging for access | record access | audit scope | Security/compliance owner | audit policy | audit completeness test | unaudited real-data access | no audit approval |
| retention schedule | define lifecycle | retention period | Legal/data owner | retention schedule | lifecycle test | retained real data | no retention approval |
| deletion workflow design | delete where allowed | deletion process | Legal/data owner | deletion design | deletion test | deletion claims | no deletion approval |
| export workflow design | control exports | export process | Legal/data/security owners | export design | export audit test | real-data export | no export approval |
| backup retention | govern backups | backup lifecycle | Operations/security owner | backup retention policy | restore/delete test | real-data backups | no backup approval |
| archival policy | govern archival | archive scope | Legal/data owner | archive policy | archive retrieval test | archival claims | no archive approval |
| data subject request handling | handle DSR requests | request workflow | Legal/data owner | DSR runbook | request simulation | DSR operation | no DSR approval |
| record correction process | correct records safely | correction process | Clinical/legal owner | correction policy | correction test | correction workflow | no correction approval |
