# Program 1 Phase R6 - Operational Readiness Gate Matrix

No operational readiness gate is closed by Phase R.

No go-live boundary is lifted by Phase R.

No production-readiness boundary is lifted by Phase R.

No real-data boundary is lifted by Phase R.

All existing prohibitions remain active.

| Gate Name | What It Protects | Current Status | Required Prerequisites | Required Owner Types | Required Evidence | Required Validation/Review | Can Phase R Close This Gate? | Reason Not Closed | Explicit Prohibition Still Active |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| operational model gate | operating model | not closed, not implemented, not executed, not validated, not approved | operating model | Product/operations owners | reviewed model | owner review | no | planning only | no operational approval |
| monitoring design gate | monitoring scope | not closed | monitoring plan | Operations/security owners | design evidence | design review | no | no implementation | no monitoring readiness |
| monitoring implementation gate | live monitoring | not closed | tooling and signals | Operations owner | monitoring evidence | alert tests | no | no tooling added | no monitoring implementation |
| alerting implementation gate | live alerts | not closed | alert rules | Operations/security owners | alert evidence | alert drill | no | no alerting added | no alerting implementation |
| incident response plan gate | incident process | not closed | incident runbooks | Security/operations owners | runbook evidence | tabletop review | no | no drill | no incident readiness |
| incident response drill gate | response proof | not closed | incident plan | Security/operations owners | drill report | drill review | no | not executed | no incident approval |
| privacy breach drill gate | privacy response | not closed | breach runbook | Legal/privacy owners | tabletop report | legal/privacy review | no | not executed | no breach readiness |
| clinical safety incident drill gate | safety response | not closed | safety runbook | Clinical/product owners | drill report | clinical review | no | not executed | no clinical safety readiness |
| rollback plan gate | rollback criteria | not closed | rollback plan | Engineering/operations owners | rollback plan | plan review | no | no approval | no rollback readiness |
| rollback test gate | rollback proof | not closed | rollback procedure | Engineering/operations owners | rollback report | drill review | no | not executed | no rollback validation |
| backup plan gate | backup scope | not closed | backup plan | Operations/security owners | backup policy | backup review | no | no validation | no backup readiness |
| restore test gate | restore proof | not closed | restore procedure | Operations/engineering owners | restore report | restore review | no | not executed | no restore validation |
| disaster recovery tabletop gate | DR readiness | not closed | DR plan | Operations/security owners | tabletop report | DR review | no | not executed | no DR readiness |
| operator runbook gate | operator guidance | not closed | runbooks | Operations/product owners | runbook set | runbook review | no | no rehearsal | no operator readiness |
| operator training gate | operator readiness | not closed | training materials | Operations owners | training records | training review | no | no training completed | no operator authorization |
| support model gate | support process | not closed | support plan | Operations/product owners | support model | support rehearsal | no | no live workflow | no support obligation |
| release procedure gate | release safety | not closed | release process | Product/operations owners | release checklist | release rehearsal | no | no approval | no release readiness |
| post-release verification gate | release verification | not closed | verification process | QA/operations owners | verification report | review | no | no deployment | no production verification |
| real-data operational gate | real-data operations | not closed | all real-data ops controls | Legal/privacy/security/operations owners | real-data ops package | formal review | no | prerequisites open | no real patient data approval |
| production operational gate | production operations | not closed | all operational gates | Product/security/operations owners | operational readiness package | formal review | no | prerequisites open | no production approval |
| go-live authorization gate | live use | not closed | production authorization | Required owners | go-live package | formal authorization | no | all gates open | no go-live authorization |
