# PR #3 final scope architecture

Status: implemented on the PR #3 remediation branch; synthetic validation
only; not production authorization.

## Root cause

The original defects were instances of one architectural error:

```text
permission check → global object load → optional tenant comparison
```

Permissions answered what an actor may do but not which tenant-owned object the
actor may use. Global patient identity and guessed object IDs could therefore
become accidental authorization boundaries.

The remediation replaces that pattern with:

```text
resolved security context → canonical scoped query → non-enumerating denial
```

## Final boundary model

Five explicit contexts cover the application:

1. `GlobalIdentityContext` exposes only minimal patient identity and
   appointment-conflict information.
2. `ClinicOperationalContext` requires active clinic membership and clinic
   equality for appointments, journeys, reception, rooms and activities.
3. `ClinicBillingContext` requires active clinic membership and immutable
   invoice clinic provenance.
4. `InstitutionClinicalContext` requires medical category, clinical
   permission, institution membership and exact institution provenance.
5. `SystemSecurityAuditContext` requires explicit audit/security authority and
   never implies unrestricted PHI access.

The implementation uses small SQLAlchemy loaders and existing dependencies,
not a policy DSL or a new authorization framework.

## Structural controls

- `billing_access.py` scopes invoices, invoice children and payments through
  the active clinic.
- `clinical_scope.py` resolves institution access for episodes, plans and
  derived clinical objects.
- `clinical_document_access.py` remains the source boundary for documents and
  signed reports.
- `audit_access.py` returns tenant-scoped audit metadata through a safe DTO.
- API keys are fixed to one clinic and institution and cannot be switched with
  a request header.
- Patient identity responses use `PatientIdentityOut`; free-text clinic notes
  and PHI children are excluded.
- Appointment patient identity is immutable after creation so linked clinical,
  operational and financial provenance cannot be silently reassigned.

## Provenance and legacy behavior

Migrations `0064`–`0066` add institution provenance to clinical aggregates and
tenant provenance to audit events and API keys. Backfill uses only
unambiguous existing relationships. Missing or conflicting provenance remains
unresolved and is denied by standard reads.

`NULL` never means “all clinics” or “all institutions”.

## Audit boundary

The standard audit response is an allowlisted projection containing event,
actor, tenant, object, action, status, reason, request and changed-field
metadata. It excludes raw before/after bodies, clinical text, diagnoses,
report content, tokens, cookies, headers and exception payloads.

Financial events preserve only material structured transaction values required
for accountability. Narrative notes and payment references remain excluded
from the generic projection.

## Validation model

The security regression matrix verifies same-scope access and negative
foreign-object behavior across billing, episodes/plans, findings,
open questions, evidence, documents, signed reports, summaries and audit.
PostgreSQL-backed tests validate tenant predicates and migration backfill.
DB-backed browser tests validate that API enforcement remains effective through
the user-facing integration.

The detailed endpoint inventory is in
[`security-scope-inventory.md`](security-scope-inventory.md). Full evidence and
measured test counts are in
[`pr3-scope-and-audit-remediation.md`](pr3-scope-and-audit-remediation.md).

## PR #4 recovery impact

PR #4 remains unchanged. Its separate recovery update must recognize Alembic
head `0066`, preserve all tenant provenance and unresolved states, include the
new provenance fields in domain hashes, and prove foreign-tenant and mixed-
source-set denial after restore. Historical metadata drift remains classified;
zero drift is not the only recovery success criterion.

## Closure boundary

This architecture closes the identified PR #3 authorization class only after
green local/CI validation and an independent adversarial review. It does not
authorize production deployment, real patient data, unrestricted system-admin
PHI access, or changes to PR #4.
