# Security scope inventory

Measured: 23 July 2026

Branch: `fix/pr3-scope-and-audit-blockers`

Base: `feature/full-stack-production-validation` at `5850342`

This inventory is the route-level review record for the PR #3 authorization
closure. The repository contains 270 FastAPI route decorators and 260
registered `/api` route-method pairs. Every route
module was searched for direct ID loads, patient-only child queries, nullable
tenant predicates, permission-only authorization, and client-controlled tenant
provenance. Nineteen route modules required changes.

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
| patient create/list/duplicates/identity detail and global search | Patient identity | global identity | authenticated identity workflow only | explicit identity column projection and typed DTO; narrative notes excluded | patient/scheduling permission | `test_patient_oib.py`, `test_pr3_fourth_security_operational_projections.py` | intentional global identity |
| patient appointment availability | Appointment availability | global identity | global patient time-conflict metadata only | availability projection | scheduling permission | `test_appointments.py` | intentional global availability |
| appointment CRUD, status and slot routes | Appointment | clinic operations | active clinic, except explicit global patient overlap check; unresolved rooms denied | exact active-clinic room validation and scoped appointment loader | appointment permission | `test_appointments.py` | enforced |
| appointment clinical-readiness preview, snapshots and acknowledgments | Clinical readiness | institution clinical | medical-staff category plus route permission and appointment clinic scope | medical guard before object resolution; readiness service requires authorized medical actor | readiness/appointment permission plus medical category | `test_pr3_third_security_readiness.py`, `test_security_scope_route_registry.py` | enforced |
| patient-journey CRUD and transition routes | PatientJourney | clinic operations | active clinic | journey parent loader plus narrow reception identity projection; no patient notes | journey permission | `test_patient_journeys.py`, `test_pr3_fourth_security_operational_projections.py` | enforced |
| journey activity, check-in, encounter, preparation, closure and timeline routes | journey children | clinic operations | scoped journey parent | parent-first active-clinic loader | route-specific journey permission | journey route suites and `test_remaining_patient_scope.py` | enforced |
| reception and daily-dashboard routes | reception projection | clinic operations | active clinic | clinic-filtered dashboard/journey query | reception/dashboard permission | dashboard and check-in suites | enforced |
| package preview, booking and materialization | package activities | clinic operations | active clinic and exactly same-clinic room/provider resources | scoped catalog and appointment services | scheduling/catalog permission | `test_catalog_governance.py` | enforced |
| appointment-material compatibility routes | material consumption | clinic operations | active clinic appointment | scoped appointment loader | material permission | inventory and remaining-scope suites | enforced |
| invoice list/create/detail/update/issue | Invoice | clinic billing | invoice clinic equals active clinic | `get_active_clinic_invoice` and scoped list query | billing permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| invoice line CRUD | InvoiceLine | clinic billing | scoped parent invoice | invoice-first loader | billing permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| payment create/list and mark-paid | PaymentTransaction | clinic billing | scoped parent invoice; parent immutable | invoice-first loader | payment permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| journey billing prepare, payment record and payment defer | journey billing projection | clinic billing | active-clinic journey and its invoice | scoped journey parent plus billing validator | billing/payment permission plus membership | journey-closure and route-registry suites | enforced |
| appointment draft-invoice | Invoice | clinic billing | appointment and produced invoice in active clinic | scoped appointment loader | billing permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| patient invoice list | Invoice | clinic billing | active clinic | invoice clinic predicate | billing read permission plus membership | `test_pr3_scope_audit_blockers.py` | enforced |
| episode list/detail/create/update/close | ClinicalEpisode | institution clinical | exact authorized institution | `get_institution_episode` and institution list predicate | medical category and clinical permission | `test_pr3_scope_audit_blockers.py` | enforced |
| episode appointment/timeline routes | episode projection | institution clinical | scoped episode parent and institution-consistent children | episode-first loader | clinical read permission | episode and blocker suites | enforced |
| clinical-plan list/active/generate/update/reject/confirm | ClinicalPlan | institution clinical | exact authorized institution | scoped episode or `get_institution_clinical_plan` | clinical-plan permission | `test_pr3_scope_audit_blockers.py` | enforced |
| patient clinical record | clinical aggregation | institution clinical | selected authorized institution | institution-exact source selection | clinical read permission | clinical-record tests | enforced |
| finding list/detail | ClinicalFinding | institution clinical | exact authorized institution | institution predicate in SQL | clinical read permission | finding read API and blocker suites | enforced |
| open-question list/detail | ClinicalOpenQuestion | institution clinical | exact authorized institution | institution predicate in SQL | clinical read permission | open-question read API and blocker suites | enforced |
| evidence timeline | derived evidence | institution clinical | exact institution source set | institution-filtered evidence builder | clinical read permission | evidence-timeline and DB-backed browser suites | enforced |
| clinical-summary and readiness routes | derived clinical projection | institution clinical | one official reviewed source set from one institution; unresolved evidence is explicit review-required limitation | exact-source-set validator and unresolved-evidence projection | summary/readiness permission | readiness snapshot and security suites | enforced |
| clinical-document list/search/detail/download/write/review/addendum | ClinicalDocument | institution clinical | exact document institution; unresolved and unclassified denied | canonical clinical-document access service; embedded patient data uses an exact four-field identity allowlist; manual and database defaults are `unclassified` until human review | document operation permission | document provenance suites, exact patient-projection contract tests, `test_pr3_fourth_security_document_classification.py` | enforced |
| signed-report view/print/addendum/delivery/history | SignedReport | institution clinical | exact report/document institution | report service through scoped document | report permission | signed-report security suites | enforced |
| clinical-form routes | ClinicalFormInstance | institution clinical | scoped journey/activity/document parent | parent-first loaders | form permission | clinical-form suites | enforced |
| pathology routes | PathologyCase/Specimen | institution clinical | scoped journey and clinical parent | parent-first scoped loader | pathology permission | pathology suites | enforced |
| laboratory order/result routes | LaboratoryOrder | institution clinical | direct institution provenance | institution predicate; unresolved denied | laboratory permission | laboratory and remaining-scope suites | enforced |
| therapy routes | Therapy | institution clinical | direct institution provenance | institution predicate; unresolved denied | therapy permission | therapy and remaining-scope suites | enforced |
| workflow clinical tasks | WorkflowTask | institution clinical | direct institution provenance | institution predicate; unresolved denied | workflow permission | `test_remaining_patient_scope.py` | enforced |
| audit access-event write | SensitiveAccessEvent | system/audit write | provenance derived by backend; direct audit references loaded and authorized | validated request/object context and exact returned ORM event | authenticated controlled event write | `test_audit.py`, PostgreSQL remediation suite | enforced |
| audit-log list | AuditLog | system security audit | active clinic for standard view; null and foreign scope denied | `list_active_clinic_audit_events` | explicit audit permission plus membership | audit and blocker suites | enforced |
| API-key issuance and AI intake | ApiKey/limited intake | tenant integration | fixed key clinic and institution | `require_tenant_clinic`; header cannot switch tenant | explicit key scopes | auth-permission and blocker suites | enforced |

Anonymous rejected-session security signals use bounded, database-atomic
five-minute aggregation. The aggregation fingerprint contains only sanitized
event classification and normalized route metadata. It is not a credential,
identity, IP-address, or patient fingerprint.

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

The lightweight registry gate classifies all 260 current `/api` route-method
pairs and fingerprints the sorted path, method and context projection. Any
addition, removal, move or reclassification changes the fingerprint and fails
CI until the route inventory is explicitly reviewed. This includes financial
mutations located outside `inventory.py`.

Modules classified wholly as `InstitutionClinicalContext` additionally declare
the shared `require_medical_staff` router dependency. Mixed modules enforce
the same medical-category rule in their canonical scoped loaders. Therefore,
an administrative role cannot convert broad permissions into clinical PHI
access, and new endpoints in wholly clinical modules fail closed.
