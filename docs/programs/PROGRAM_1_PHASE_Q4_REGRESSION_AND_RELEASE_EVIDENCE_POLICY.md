# Program 1 Phase Q4 - Regression and Release Evidence Policy

Current demo checks are useful but do not constitute production validation.

| Requirement | Purpose | When Required | Owner Type | Required Evidence | Acceptance Criteria Concept | Current Status | Non-Approval Statement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pre-release regression checklist | standardize release checks | every release candidate | QA/operations owner | completed checklist | all required checks accounted for | planned only | no release approval |
| backend test suite evidence | prove backend regression status | every backend release | QA/engineering owner | suite output | expected pass threshold | planned only | no production validation |
| frontend build/typecheck/smoke evidence | prove frontend baseline | every frontend release | QA/frontend owner | typecheck/build/smoke output | stable build and safe UI | planned only | no deployment approval |
| migration upgrade evidence | verify DB upgrade | every migration release | Engineering owner | alembic output | upgrade succeeds | planned only | no production DB approval |
| migration rollback evidence | verify rollback plan | before production claim | Engineering/operations owner | rollback drill evidence | recoverable state | planned only | no rollback validation |
| API contract evidence | verify API boundaries | every API change | QA/product owner | contract tests | shape stable, forbidden fields absent | planned only | no API approval |
| documentation consistency evidence | prevent maturity overclaim | every governance release | Product/legal owner | doc review | no forbidden claims | planned only | no legal approval |
| safety boundary evidence | preserve no-go decisions | every clinical release | Clinical/QA owner | safety matrix output | no prohibited behavior | planned only | no safety certification |
| synthetic-data evidence | verify demo data only | every demo release | Data governance owner | demo data audit | no real-like records | planned only | no real-data approval |
| read-only/write-prevention evidence | prove no writes | every read-only release | QA/security owner | no-write tests | write attempts absent/denied | planned only | no write boundary validation |
| security/privacy evidence | verify risk posture | before real-data or production consideration | Security/privacy owner | security/privacy report | risks reviewed | planned only | no security approval |
| access/audit evidence | verify controls | before real-data or production consideration | Security/compliance owner | access/audit tests | allow/deny/audit completeness | planned only | no access/audit validation |
| release notes | communicate scope | every release candidate | Product owner | release notes | boundaries stated | planned only | no production claim |
| known limitations | communicate constraints | every release candidate | Product/legal owner | limitations doc | no-go areas visible | planned only | no live-use approval |
| go/no-go matrix | record decision state | every phase/release | Product/governance owner | matrix | gates explicit | planned only | no gates closed |
| operator sign-off checklist | verify operator readiness | demo and future release | Operations owner | checklist | operator can execute safely | planned only | no operator approval |
| evidence archive location | preserve evidence | every release candidate | QA/operations owner | archive index | evidence traceable | planned only | no archive created |
| post-release verification | verify deployed state | future deployments only | Operations/QA owner | verification report | expected state confirmed | planned only | no deployment approval |
