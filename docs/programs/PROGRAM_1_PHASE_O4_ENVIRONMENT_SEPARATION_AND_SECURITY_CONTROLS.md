# Program 1 Phase O4 - Environment Separation and Security Controls

No environment is approved for real patient data by Phase O.

No production environment is approved by Phase O.

| Control Name | Purpose | Environment Affected | Required Owner Type | Required Evidence | Required Future Validation | Current Status | Explicit Prohibition Still Active |
| --- | --- | --- | --- | --- | --- | --- | --- |
| separate demo/test/staging/production environments | prevent environment mixing | all | Engineering/operations owner | environment architecture | isolation tests | not approved | no real-data environment |
| synthetic-only demo environment | keep demo fake | demo | Data/product owner | demo data policy | demo data audit | demo-only | no real data in demo |
| real-data environment isolation | isolate future real data | future production | Security/operations owner | isolation design | penetration/access tests | not implemented | no real-data deployment |
| secrets management | protect credentials | all | Security/operations owner | secrets policy | rotation test | not production-approved | no live secrets claim |
| encryption in transit | protect network traffic | all | Security owner | TLS policy | security test | not validated for production | no real-data transport |
| encryption at rest | protect stored data | data stores | Security/operations owner | encryption design | storage verification | not validated | no real-data storage |
| backup encryption | protect backups | backups | Security/operations owner | backup encryption policy | restore verification | not validated | no real-data backups |
| database access restrictions | limit DB access | database | Security/engineering owner | DB access policy | negative access tests | not production-approved | no real-data DB access |
| logging redaction | prevent PHI in logs | logging | Security/engineering owner | redaction policy | log scan tests | not validated | no PHI logging |
| attachment/document storage controls | protect documents | object/file storage | Security/data owner | storage control design | storage access tests | not approved | no real documents |
| network restrictions | reduce exposure | network | Security/operations owner | network design | network review | not production-approved | no live exposure |
| dependency/security patch process | maintain security | app/runtime | Engineering/security owner | patch policy | update rehearsal | not production-approved | no production claim |
| vulnerability scanning | detect risks | code/infrastructure | Security owner | scan process | scan evidence review | not production-approved | no security clearance |
| security review cadence | repeat review | security program | Security owner | review calendar | review evidence | not established | no security approval |
| infrastructure access logging | trace infra access | infrastructure | Operations/security owner | infra logging policy | audit sample | not validated | no real-data infra access |
| local development real-data prohibition | keep PHI out of local dev | local dev | Engineering/security owner | local dev policy | developer workflow review | active prohibition | no local real data |
