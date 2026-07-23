# Security scope inventory

Measured: 23 July 2026

Branch: `fix/pr3-scope-and-audit-blockers`

Base: `feature/full-stack-production-validation` at `5850342`

This inventory is the route-level review record for the PR #3 authorization
closure. The repository contains 270 FastAPI route decorators. Every route
module was searched for direct ID loads, patient-only child queries, nullable
tenant predicates, permission-only authorization, and client-controlled tenant
provenance. Seventeen route modules required changes.

The inventory records security boundaries, not business ownership. A global
`Patient` row is identity data; it never grants access to clinical, financial,
operational, or audit children.

## Canonical contexts

| Context | Required boundary | Canonical enforcement |
| --- | --- | --- |
| `GlobalIdentityContext` | authenticated minimal identity or scheduling-conflict visibility | dedicated identity DTO; no notes or PHI children |
| `ClinicOperationalContext` | permission, active membership, object clinic equals active clinic | parent-first clinic loader |
| `ClinicBillingContext` | billing permission, active membership, invoice clinic equals active clinic | `billing_access` invoice/appointment loaders |
| `InstitutionClinicalContext` | medical category, clinical permission, active membership in the institution, exact object institution | `clinical_scope` and clinical-document access loaders |
| `SystemSecurityAuditContext` | explicit audit/security permission and applicable event provenance | clinic-scoped safe audit projection; null scope denied |

`NULL` clinic or institution provenance is unresolved, not global. Standard
users and tenant API keys cannot read unresolved legacy rows.

## Route inventory

The test-group column identifies the regression suite that contains same-scope
and foreign-object assertions. Routes sharing one parent-first loader are
grouped to keep this record maintainable; every HTTP operation in the listed
path family was inspected.

| Route family and methods | Object | Classification | Expected scope | Current loader/filter | Permission boundary | Foreign-object test group | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| patient create/list/duplicates/identity detail | Patient identity | global identity | authenticated identity workflow only | `PatientIdentityOut`; narrative notes excluded | patient/scheduling permission | `test_patient_oib.py` | intentional global identity |
| patient appointment availability | Appointment availability | global identity | global patient time-conflict metadata only | availability projection | scheduling permission | `test_appointments.py` | intentional global availability |
| appointment CRUD, status and slot routes | Appointment | clinic operations | active clinic, except explicit global patient overlap check | active-clinic appointment loader and clinic validation | appointment permission | `test_appointments.py` | enforced |
| patient-journey CRUD and transition routes | PatientJourney | clinic operations | active clinic | journey parent loader | journey permission | `test_patient_journeys.py` | enforced |
| journey activity, check-in, encounter, preparation, closure and timeline routes | journey children | clinic operations | scoped journey parent | parent-first active-clinic loader | route-specific journey permission | journey route suites and `test_remaining_patient_scope.py` | enforced |
| reception and daily-dashboard routes | reception projection | clinic operations | active clinic | clinic-filtered dashboard/journey query | reception/dashboard permission | dashboard and check-in suites | enforced |
| package preview, booking and materialization | package activities | clinic operations | active clinic and same-clinic resources | scoped catalog and appointment services | scheduling/catalog permission | `test_catalog_governance.py` | enforced |
| appointment-material compatibility routes | material consumption | clinic operations | active clinic appointment | scoped appointment loader | material permission | inventory and remaining-scope suites | enforced |
| invoice list/create/detail/update/issue | Invoice | clinic billing | invoice clinic equals active clinic | `get_active_clinic_invoice` and scoped list query | billing permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| invoice line CRUD | InvoiceLine | clinic billing | scoped parent invoice | invoice-first loader | billing permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| payment create/list and mark-paid | PaymentTransaction | clinic billing | scoped parent invoice; parent immutable | invoice-first loader | payment permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| appointment draft-invoice | Invoice | clinic billing | appointment and produced invoice in active clinic | scoped appointment loader | billing permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| patient invoice list | Invoice | clinic billing | active clinic | invoice clinic predicate | billing read permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| episode list/detail/create/update/close | ClinicalEpisode | institution clinical | exact authorized institution | `get_institution_episode` and institution list predicate | medical category and clinical permission | `test_pr3_scope_audit_blockers.py` | enforced |
| episode appointment/timeline routes | episode projection | institution clinical | scoped episode parent and institution-consistent children | episode-first loader | clinical read permission | episode and blocker suites | enforced |
| clinical-plan list/active/generate/update/reject/confirm | ClinicalPlan | institution clinical | exact authorized institution | scoped episode or `get_institution_clinical_plan` | clinical-plan permission | `test_pr3_scope_audit_blockers.py` | enforced |
| patient clinical record | clinical aggregation | institution clinical | selected authorized institution | institution-exact source selection | clinical read permission | clinical-record tests | enforced |
| finding list/detail | ClinicalFinding | institution clinical | exact authorized institution | institution predicate in SQL | clinical read permission | finding read API and blocker suites | enforced |
| open-question list/detail | ClinicalOpenQuestion | institution clinical | exact authorized institution | institution predicate in SQL | clinical read permission | open-question read API and blocker suites | enforced |
| evidence timeline | derived evidence | institution clinical | exact institution source set | institution-filtered evidence builder | clinical read permission | evidence-timeline and DB-backed browser suites | enforced |
| clinical-summary and readiness routes | derived clinical projection | institution clinical | one official reviewed source set from one institution | exact-source-set validator | summary/readiness permission | readiness snapshot and security suites | enforced |
| clinical-document list/search/detail/download/write/review/addendum | ClinicalDocument | institution clinical | exact document institution; unresolved denied | canonical clinical-document access service | document operation permission | document provenance security suites | enforced |
| signed-report view/print/addendum/delivery/history | SignedReport | institution clinical | exact report/document institution | report service through scoped document | report permission | signed-report security suites | enforced |
| clinical-form routes | ClinicalFormInstance | institution clinical | scoped journey/activity/document parent | parent-first loaders | form permission | clinical-form suites | enforced |
| pathology routes | PathologyCase/Specimen | institution clinical | scoped journey and clinical parent | parent-first scoped loader | pathology permission | pathology suites | enforced |
| laboratory order/result routes | LaboratoryOrder | institution clinical | direct institution provenance | institution predicate; unresolved denied | laboratory permission | laboratory and remaining-scope suites | enforced |
| therapy routes | Therapy | institution clinical | direct institution provenance | institution predicate; unresolved denied | therapy permission | therapy and remaining-scope suites | enforced |
| workflow clinical tasks | WorkflowTask | institution clinical | direct institution provenance | institution predicate; unresolved denied | workflow permission | `test_remaining_patient_scope.py` | enforced |
| audit access-event write | SensitiveAccessEvent | system/audit write | provenance derived by backend | validated request/object context | authenticated controlled event write | `test_audit.py` | enforced |
| audit-log list | AuditLog | system security audit | active clinic for standard view; null and foreign scope denied | `list_active_clinic_audit_events` | explicit audit permission plus membership | audit and blocker suites | enforced |
| API-key issuance and AI intake | ApiKey/limited intake | tenant integration | fixed key clinic and institution | `require_tenant_clinic`; header cannot switch tenant | explicit key scopes | auth-permission and blocker suites | enforced |

## Loader convention

Sensitive handlers follow:

```text
resolved actor/security context
→ scope predicate inside the SQL query
→ object or non-enumerating 404/deny
→ mutation using the same resolved parent
```

Direct `session.get(Model, id)` remains allowed for authentication records,
global identity records, and already-scoped child resolution only when no PHI
or financial authorization is inferred from the ID.

## Regression coverage

The negative matrix covers:

- permission without active membership;
- membership without permission;
- foreign clinic or institution;
- user in both tenants with the other tenant active;
- inactive membership;
- guessed object ID;
- tenant API key attempting a scope switch;
- unresolved legacy provenance;
- mixed-institution derived source sets;
- system administrator without an explicit PHI grant;
- PHI/token sentinels in audit API output.

The route families above are also exercised by PostgreSQL integration and
DB-backed browser tests. Frontend hiding is never treated as authorization.
