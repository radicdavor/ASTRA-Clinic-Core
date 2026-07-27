# Lean Core authorization map

Status: Module 3.5 Increment B

## Decision path

ASTRA uses two deliberately small authorization entry points:

1. `require_permission(name)` for institution-wide clinical reads or other
   operations that do not use the active-clinic boundary;
2. `require_active_clinic(name)` for clinic-scoped operations. It validates the
   permission, signed-in user, active memberships and `X-Clinic-Id`, then returns
   `CurrentUserContext`.

Object policy remains in scoped loaders or focused service functions. The UI
capability flags are hints only; every write endpoint repeats the authoritative
backend policy check.

## Route and policy map

| Route group | Permission entry point | Scope | Author/status policy | Canonical loader or service |
| --- | --- | --- | --- | --- |
| patient directory and identity | `require_active_clinic("patients.read")` | global patient identity after active-clinic authorization | none | bounded patient query; identity is not duplicated per clinic |
| clinic patient operations | `require_active_clinic(...)` | active clinic | operation-specific | `get_scoped_patient` / `patient_in_active_clinic_statement` |
| appointments and schedule | `require_active_clinic(...)` | active clinic | appointment status/conflict service | clinic predicate in appointment query; route-local loaded appointment helpers remain where relationship shape differs |
| patient journeys | `require_active_clinic(...)` | active clinic | transition state machine | clinic predicate in journey query / `get_scoped_journey` where a simple graph is sufficient |
| dashboard and reception | `require_active_clinic(...)` | active clinic | role-aware projection and check-in rules | dashboard projection query / scoped journey loaders |
| billing and payments | clinic billing permissions | active clinic | invoice/payment state services | invoice queries must contain clinic/journey provenance |
| institution clinical record metadata | current actor plus clinical read policy | institution | clinical classification only | `resolve_actor_institution_context` and `institution_scoped_clinical_documents_statement` |
| clinical document detail/source | current actor plus clinical read policy | institution | clinical classification; medical professional category | `get_institution_scoped_clinical_document_for_read` |
| clinical draft edit | current actor | institution + author | own editable draft; signed is immutable | `get_authored_draft_for_edit` / `can_edit_clinical_draft` |
| signed report and print | report permission plus clinical read policy | institution and exact source document | integrity hash must pass | report loader plus `get_institution_scoped_clinical_document_for_read` and `verify_report_integrity` |
| addendum | addendum permission plus clinical read policy | institution and exact signed report version | final/signed source; authenticated author | `create_document_addendum` |
| source classification | review permission | source document scope | `unclassified` until explicit human classification | document-ingestion classification service and route |
| membership administration | administrative permission | clinic/institution membership | active membership rules | membership routes and `active_clinic_memberships` |

## Canonical policy functions

The current minimal policy vocabulary is:

- `require_permission`: permission gate;
- `require_active_clinic`: permission plus active membership and clinic context;
- `get_scoped_patient`: clinic-associated patient operation loader;
- `get_scoped_journey`: clinic-scoped journey loader;
- `actor_is_medical_staff`: professional category plus institution-read permission;
- `resolve_actor_institution_context`: explicit institution selection policy;
- `institution_scoped_clinical_documents_statement`: metadata-list scope;
- `get_institution_scoped_clinical_document_for_read`: classified clinical
  document read, provenance and deduplicated read audit;
- `get_authored_draft_for_edit` / `can_edit_clinical_draft`: author and mutable
  status enforcement;
- `create_document_addendum`: immutable-source addendum policy;
- `clinical_document_capabilities`: shared read-only projection of edit, review
  and addendum actions.

No generic policy engine, DSL, global authorization cache or new abstraction
layer was added.

## Duplicate logic removed in Increment B

Clinical document detail and institution clinical-record metadata previously
calculated `can_edit` and `can_add_addendum` independently with slightly
different status expressions. Both now use `clinical_document_capabilities`,
which derives flags from the same constants used by authoritative write policy.
This removes two route-level implementations without changing write checks.

## Deliberately retained boundaries

- Appointment loaders retain route-specific relationship options; forcing them
  into one generic loader would obscure query shape and add a policy layer.
- Institution clinical reads use `Actor`, not active-clinic context, because an
  authorized medical user may read clinical records across clinics in the same
  institution.
- Patient identity search remains institution/global identity reuse after the
  caller has an active clinic; clinical and financial associations remain
  scoped.
- Permission and membership changes are evaluated per request. There is no
  long-lived authorization cache, so revocation remains immediate.
- Existing permission-only legacy/readiness endpoints were not behaviorally
  respecified in an optimization increment. Any scope change requires a
  separate product/security decision and regression plan.

## Regression matrix

`test_institution_clinical_document_access.py` covers:

- permission with and without medical professional category;
- same-institution and other-institution access;
- physician and nurse reads;
- administrative denial;
- author, non-author and unknown legacy author;
- draft, reviewed and signed states;
- clinical, financial and unclassified records;
- addendum authorization and exact-source immutability;
- immediate permission revocation;
- metadata-only clinical-record listing and access audit.

Clinic membership, active-clinic, session, CSRF, billing-isolation and
appointment-scope matrices remain in their dedicated regression suites.
