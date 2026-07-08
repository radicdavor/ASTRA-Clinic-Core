# Program 1 Phase R3 - Incident Response and Escalation Model

Severity levels are planning constructs only, not an active incident management system.

- SEV-0 - potential patient safety, PHI/PII, or production boundary event.
- SEV-1 - major system/security/privacy risk.
- SEV-2 - degraded functionality or operational risk.
- SEV-3 - minor defect, documentation, or support issue.

| Incident Type | Risk Addressed | Initial Triage Owner Type | Escalation Owner Types | Required Future Evidence | Required Future Response Procedure | Required Future Communication Boundary | Current Status | Non-Operationalization Statement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| system outage | unavailable system | Operations owner | Engineering/product owners | outage runbook | incident triage | no production claim | planned only | no incident tooling |
| degraded performance | poor operation | Operations owner | Engineering owner | performance runbook | degradation response | no clinical assurance | planned only | no monitoring |
| data integrity concern | incorrect records | Engineering/data owner | Clinical/security owners | integrity checklist | isolate and review | no patient notification | planned only | no live workflow |
| unauthorized access concern | access misuse | Security owner | Privacy/legal owners | access incident runbook | revoke/investigate | privacy-safe comms | planned only | no access tooling |
| audit logging concern | missing accountability | Security/compliance owner | Legal/operations owners | audit incident plan | preserve evidence | no validation claim | planned only | no audit runtime |
| privacy/PHI/PII concern | privacy harm | Privacy owner | Legal/security owners | privacy runbook | privacy triage | legal-reviewed comms | planned only | no PHI processing |
| suspected real-data boundary violation | real-data misuse | Data/privacy owner | Legal/security owners | boundary incident plan | stop and isolate | no real-data approval | planned only | no ingestion path |
| security incident | system compromise | Security owner | Operations/legal owners | security runbook | containment | security-approved comms | planned only | no security tooling |
| clinical safety incident | patient safety concern | Clinical owner | Product/legal/security owners | safety incident plan | clinical escalation | no autonomous advice | planned only | no clinical incident workflow |
| incorrect advisory/disclaimer concern | unsafe wording | Product owner | Clinical/legal owners | wording review plan | remove/clarify | non-approval language | planned only | no live support process |
| patient messaging boundary violation attempt | unauthorized contact | Product/legal owner | Security/clinical owners | no-go incident plan | block/review | no patient contact | planned only | no messaging |
| appointment mutation boundary violation attempt | workflow mutation | Operations/product owner | Security/clinical owners | no-go incident plan | block/review | no status change | planned only | no mutation |
| clinical write workflow boundary violation attempt | unsafe write | Clinical/product owner | Security/legal owners | no-go incident plan | block/review | no clinical decision | planned only | no write workflow |
| Task engine or Outcome Evidence boundary violation attempt | prohibited semantics | Product/clinical owner | Legal/security owners | no-go incident plan | block/review | no outcome/task claim | planned only | no Task/Outcome |
| deployment/release incident | bad release | Operations owner | Engineering/product owners | release incident plan | rollback decision | no production claim | planned only | no deployment tooling |
| backup/restore incident | recovery failure | Operations owner | Engineering/security owners | recovery incident plan | restore triage | no recovery claim | planned only | no restore validation |
| vendor/subprocessor incident | third-party risk | Legal/privacy owner | Security/operations owners | vendor incident plan | vendor escalation | legal-reviewed comms | planned only | no vendor approval |
