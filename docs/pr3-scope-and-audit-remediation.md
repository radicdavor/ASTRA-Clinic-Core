# PR #3 scope and audit remediation

Measured: 22 July 2026

Branch: `fix/pr3-scope-and-audit-blockers`

Base: `feature/full-stack-production-validation`

## Decision

Clinic operations and billing use the active clinic. Clinical continuity reads
use an explicit institution provenance boundary. A global `Patient` row is
identity and duplicate-prevention data only; it is never an authorization
shortcut to clinical, operational, or financial child records.

Unresolved or conflicting legacy provenance is denied by default. No route may
interpret a null tenant field as a wildcard.

## Findings and root causes

| Finding | Root cause | Remediation |
| --- | --- | --- |
| Billing object access crossed the active-clinic boundary | invoice and payment handlers loaded objects directly by ID | centralized active-clinic invoice and appointment loaders are used before billing reads or mutations |
| Episodes and derived clinical evidence lacked durable tenant provenance | authorization was inferred transitively from global patient identity or mutable links | migrations `0064` and `0065` add conservative institution provenance and institution-scoped loaders |
| Audit reads exposed excessive payloads and lacked reliable tenant provenance | the endpoint returned raw audit rows and snapshots accepted broad model fields | clinic-scoped safe DTO, backend-derived audit provenance, changed-field projection, and a PHI-safe snapshot allowlist |
| Integration API keys were permission-scoped but not tenant-scoped | a key could authenticate without a fixed clinic and institution | migration `0066` binds new keys to the creator's active clinic and institution; legacy unscoped keys are denied |

The repository-wide same-pattern review also covered journey children,
check-in, encounter, preparation, pathology, appointment materials, package
scheduling/materialization, readiness acknowledgments, laboratory orders,
therapies, workflow tasks, appointment creation, AI intake, signed reports,
clinical document ingestion, summaries, and evidence timelines.

## Canonical scope matrix

| Surface | Data returned | Required scope | Loader or rule | Status |
| --- | --- | --- | --- | --- |
| Invoices, lines, payments | financial data | active clinic | `billing_access` clinic loaders | enforced |
| Appointment and journey operations | operational data | active clinic | active-clinic appointment/journey loaders | enforced |
| Journey activity, check-in, encounter, preparation | visit child data | scoped journey parent | parent-first active-clinic loaders | enforced |
| Episode, plan, finding, open question | clinical data | actor institution | institution provenance loaders | enforced |
| Lab orders, therapies, workflow tasks | patient clinical child data | actor institution | direct `institution_id` plus deny-by-default | enforced |
| Clinical documents and signed reports | source and signed clinical content | exact document institution | canonical clinical-document access service | enforced |
| Summaries, readiness, evidence timeline | derived clinical projection | exact permitted source set | source-linked institution validation | enforced |
| Audit list | operational audit metadata | active clinic | clinic predicate plus safe DTO | enforced |
| API-key AI intake | minimal integration data | key clinic and institution | `require_tenant_clinic` | enforced |
| Shared patient search | identity/dedup fields | authenticated scheduling permission | global identity only; no child clinical data | intentional |
| Patient appointment availability | time-conflict metadata | scheduling permission | global patient conflict visibility | intentional |

## Migration behavior

### `0064_pr3_scope_provenance`

Adds institution provenance to episodes, findings, and open questions, and
clinic/institution/scope metadata to audit events. Backfill occurs only where
existing immutable relationships agree. Conflicting or missing provenance
remains null and restricted.

### `0065_patient_clinical_child_scope`

Adds institution provenance to laboratory orders, therapies, and workflow
tasks. Backfill is conservative and does not choose an arbitrary clinic or
institution.

### `0066_api_key_tenant_scope`

Adds `clinic_id` and `institution_id` to API keys. New keys inherit the active
clinic and its institution. Existing keys are left unresolved and cannot use
tenant routes until explicitly replaced; no default tenant is guessed.

Validated migration paths:

- empty PostgreSQL database to `0066`;
- populated `0063` to `0066` with resolvable and conflicting fixtures;
- `0066 -> 0065 -> 0066`;
- `0066 -> 0062 -> 0066`;
- one Alembic head: `0066_api_key_tenant_scope`.

`alembic check` remains non-zero because of documented historical ORM/schema
metadata drift. Direct `compare_metadata` measurement reports 86 operations.
None references the new `0064`-`0066` tenant columns or constraints.

## Audit contract

The standard audit endpoint returns operational metadata only: actor type and
user ID; entity type and ID; action, status, reason code, and changed field
names; clinic, institution, scope type, request ID, and timestamp.

It does not return before/after values, free-text summaries, IP addresses,
user-agent strings, tokens, document content, clinical notes, or patient
payloads. Audit provenance is derived from validated request context or the
authoritative object, never trusted from a client body.

## API-key rules

- each newly issued key is fixed to one clinic and one institution;
- `X-Clinic-Id` cannot switch a key to another clinic;
- legacy keys with null provenance fail closed;
- API-key permission scopes do not imply user, billing, audit, or PHI access;
- the AI boundary exposes only explicitly allowed minimal operations.

## Test evidence

At the remediation HEAD before GitHub publication:

- backend fast gate: 147 passed;
- full non-integration backend: 737 passed, 2 skipped, 16 deselected;
- PostgreSQL integration: 16 passed;
- frontend: 57 Vitest tests and 4 contract tests passed;
- route-mocked Playwright: 1 passed;
- isolated DB-backed Playwright: 11 passed, including foreign invoice,
  episode, finding, open-question, and evidence-timeline denial;
- OpenAPI generated-contract check: passed;
- populated and empty migration regression gates: passed.

These are local synthetic validation results. They are not a production
deployment authorization.

## Required PR #4 recovery follow-up

PR #4 remains stacked and unchanged until PR #3 is merged to `main`. Its
separate update must:

1. accept source manifests at `0061`, `0062`, `0063`, and `0066`, record the
   actual source revision, restore, and explicitly migrate to `0066`;
2. validate `empty -> 0066`, `0061 backup -> 0066`, `0062 backup -> 0066`,
   `0063 backup -> 0066`, and `0066 backup -> 0066`;
3. include episode/finding/open-question, lab-order/therapy/workflow-task,
   audit, and API-key tenant provenance in recovery manifests and domain hash
   projections;
4. preserve clinical-document clinic/institution provenance, unresolved state,
   classification, immutable links, exact summary/readiness source sets, and
   signed-report delivery institution scope;
5. prove unresolved or conflicting restored rows remain restricted, foreign
   provenance is rejected, mixed-institution derived source sets are rejected,
   unscoped restored API keys remain unusable, and old session cookies remain
   invalid;
6. rerun recovery CI after PR #4 is retargeted to `main` following the
   owner-approved merge of PR #3.

Historical metadata drift must remain classified; `alembic check == zero` is
not the sole recovery criterion and no broad autogenerated migration is
authorized.
