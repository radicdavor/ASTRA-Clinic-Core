# Program 1 Phase M2 - Remediation Priority Matrix

P0/P1 items block any production-readiness claim.

| Item | Priority | Why It Matters | Required Evidence | Suggested Future Phase | Blocking Status |
| --- | --- | --- | --- | --- | --- |
| Clinical responsibility model | P0 | defines final authority | responsibility model and clinical owner review | N | blocks production |
| Real patient data governance model | P0 | protects PHI/PII and legal basis | GDPR/DPIA and data policy | O | blocks real data |
| Access control/RBAC model | P0 | limits sensitive access | least-privilege matrix and tests | P | blocks production |
| Audit trail completeness | P1 | supports accountability | audit coverage and retention evidence | P | blocks production claim |
| Incident response model | P1 | supports safe operations | incident runbook and drill | R | blocks production claim |
| Rollback and restore verification | P1 | protects data and uptime | restore/rollback drill | R | blocks production claim |
| Environment hardening | P1 | protects deployment | hardened environment checklist | R | blocks production claim |
| Validation evidence package | P1 | proves controls work | validation matrix and archive | Q | blocks production claim |
| Monitoring and alerting | P1 | detects failures | alert configuration and owners | R | blocks production claim |
| Operator training and runbooks | P2 | prevents misuse | training pack and sign-off | S | blocks controlled operations |
| Legal/GDPR review | P0 | prevents unlawful use | legal/compliance review | O | blocks real data |
| Patient communication prohibition/controls | P1 | prevents unsafe messaging | prohibition or approved future design | N | blocks messaging |
| Appointment mutation prohibition/controls | P1 | prevents unintended workflow mutation | prohibition or approved future design | N | blocks workflow mutation |
| Clinical write-workflow prohibition/controls | P0 | prevents unsafe clinical state changes | explicit no-go or future approval process | N | blocks write workflows |
