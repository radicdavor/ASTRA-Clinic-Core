# Production-readiness backlog

This is the canonical backlog for operational, privacy, security and clinical
readiness gaps. Technical CI, merge and evidence artifacts do not authorize
deployment, production or real patient data.

Status vocabulary: `NOT_STARTED`, `DESIGNED`, `SYNTHETICALLY_TESTED`,
`OPERATIONALLY_PROVEN`, `OWNER_ACCEPTED`, `PRODUCTION_AUTHORIZED`.

| Area | Current evidence | Gap | Owner | Entry criterion | Exit evidence | Status |
|---|---|---|---|---|---|---|
| Human usability | Automated and synthetic browser workflows | Moderated sessions with clinic roles and acceptance thresholds | Product/clinical owner | Stable synthetic candidate and protocol | Signed session results, findings and rerun decision | NOT_STARTED |
| GDPR/DPIA/DPA | Real data prohibited | Legal basis, DPIA, processor and DPA decisions | Privacy/legal owner | Defined processing purpose and providers | Approved DPIA/DPA record | NOT_STARTED |
| Retention and deletion | No production policy | Record-specific retention, deletion and legal-hold rules | Privacy/clinical owner | Data inventory | Approved policy and tested procedures | NOT_STARTED |
| Audit retention and review | Audited technical mutations | Retention, immutable storage and review cadence | Security/operations owner | Audit event inventory | Operational review and retention evidence | DESIGNED |
| Production identity and secrets | Development safety checks | Production identity provider, provisioning and rotation | Security/operations owner | Deployment topology | Tested provisioning/revocation records | NOT_STARTED |
| Encryption and KMS | Repository secret-handling rules | At-rest/in-transit design and key ownership | Security owner | Data/storage inventory | Approved KMS design and rotation drill | NOT_STARTED |
| PostgreSQL backup cadence | Synthetic backup tooling | Scheduled production cadence and monitoring | Database/operations owner | Production database design | Successful scheduled backups and alerts | SYNTHETICALLY_TESTED |
| WAL/PITR | Not implemented | WAL archive, retention and point-in-time drill | Database owner | Backup/KMS design | Timed PITR exercise | NOT_STARTED |
| Immutable off-site backup | Not implemented | Independent immutable copy and access separation | Operations/security owner | Retention and KMS decisions | Restore from verified off-site copy | NOT_STARTED |
| Production recovery drill | Synthetic PostgreSQL recovery matrix | Production-scale timed rehearsal | Incident/database owner | Approved runbook and environment | Signed drill with observed RPO/RTO | SYNTHETICALLY_TESTED |
| Monitoring | Health checks and logs | Service/database/storage metrics and dashboards | Operations owner | Deployment topology | Operational dashboard evidence | DESIGNED |
| Alerting | No production alert service | Thresholds, routing and escalation tests | Operations owner | Monitoring signals | Alert delivery and response drill | NOT_STARTED |
| On-call and incident response | No assigned production service | Owners, severity model and communication path | Organizational owner | Service ownership decision | Approved rota/runbook and exercise | NOT_STARTED |
| Dependency governance | Pinned direct files and weekly proposal config | Alert ownership, SBOM and Python hash locking | Repository/security owner | Governance PR merged | Audited update cycle and backlog | DESIGNED |
| Vulnerability disclosure | GitHub private vulnerability reporting enabled; SECURITY policy links the private advisory flow | Assigned response ownership, triage expectations and an exercised intake process | Repository owner | Assign response ownership and exercise private intake | Tested intake and documented response ownership | DESIGNED |
| SBOM | Not generated | Format, producer, retention and validation | Security/release owner | Dependency sources stable | Exact-SHA SBOM artifact | NOT_STARTED |
| Deployment topology | Local Docker Compose only | Supported proxy, TLS, network and environment design | Platform owner | Hosting decision | Reviewed deployment architecture | NOT_STARTED |
| High availability | Not implemented | Service/database redundancy and failover | Platform/database owner | Production topology | Controlled failover drill | NOT_STARTED |
| Regional recovery | Not implemented | Regional failure design and exercise | Platform owner | HA and backup design | Regional recovery drill | NOT_STARTED |
| Production rollback | Technical Git history only | Application/database rollback boundaries and runbook | Release/database owner | Deployment and migration design | Timed rollback rehearsal | NOT_STARTED |
| External provider governance | Interfaces and demo stubs | Contracts, processors, failure semantics and monitoring | Product/privacy owner | Provider selection | Approved provider and test evidence | NOT_STARTED |
| E-mail/SMS delivery semantics | Local/demo acceptance only | Delivery, bounce, retry, consent and audit semantics | Product/operations owner | Provider governance | End-to-end synthetic provider test | NOT_STARTED |
| Fiscalization | Noop/stub | Legal integration, certificates and failure handling | Finance/legal owner | Regulatory/provider decision | Certified integration evidence | NOT_STARTED |
| WCAG and assistive technology | Automated semantic checks | Full audit and human assistive-technology evaluation | Accessibility/product owner | Stable UI candidate | Findings closure and evaluation report | SYNTHETICALLY_TESTED |
| Production RPO/RTO measurement | Policy targets accepted; observed values are `null` | Timed production-like measurement and owner acceptance | Operations/database owner | Approved recovery environment | Observed RPO/RTO and verification time | OWNER_ACCEPTED |
| Real-patient-data authorization | Explicitly prohibited | All legal, privacy, security, operational and clinical gates | Organizational owner | All prerequisite evidence reviewed | Separate written authorization | NOT_STARTED |

`OWNER_ACCEPTED` for RPO/RTO means only that policy targets were accepted. It
does not mean the targets were observed or that production recovery is proven.
No row in this backlog is currently `PRODUCTION_AUTHORIZED`.
