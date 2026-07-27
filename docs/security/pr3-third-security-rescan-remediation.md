# PR #3 Third Full Security Rescan Remediation

## Scope

- Scanned PR #3 revision: `009837a1e455a236195581c9066ff0cf42ebf68c`
- Scan ID: `b810db94-8f8b-4115-9cb5-e3b001dc66b5`
- Coverage: 117/117 review rows
- Reportable findings: 2 Medium and 1 Low
- Previously remediated findings: the previous eight findings were not reproduced
- Hardening decision: proportional local fixes; no new architecture

This is a defensive, sanitized remediation record. It excludes exploit
instructions, credentials, patient information and local scan-artifact paths.

## Affected surfaces

| Finding | Confirmed surface | Sibling surfaces reviewed |
| --- | --- | --- |
| Operational appointment projections exposed free text | appointment list/detail/create/update, daily schedule, reception, web intake and AI appointment responses | package booking and journey headers retain opaque operational references; explicit patient and clinical detail remain separate authorized surfaces |
| Clinical readiness lacked a medical-category guard | preview, snapshot capture/history/detail/supersession and acknowledgment list/detail | technical `/ready` health checks remain system readiness and are intentionally unaffected |
| Audit reference lookup exposed object existence | direct `audit_log.viewed` reference resolution | clinical documents, signed reports, journeys/forms and invoices already collapse inaccessible objects to not-found or use scoped lookup; unrelated appointment resource-conflict validation is not an audit-object lookup |

## Root causes and fixes

### Narrow operational appointment contract

The shared appointment response inherited a broad patient serializer and
therefore included free-text patient notes. The remediation introduces explicit
operational identity projections and uses them consistently across operational
appointment surfaces. The response shape is stable for every role and API-key
caller; it is not conditionally filtered by role.

Operational responses now contain scheduling identity, time, service, provider,
room and status data only. They do not contain patient notes, appointment notes,
clinical notes, summaries, findings, therapy or diagnoses. Clinical detail is
still retrieved through its existing separately authorized routes.

### Medical category at the clinical-readiness boundary

Every patient clinical-readiness route now requires both its existing
permission/clinic context and the canonical `medical_staff` professional
category. The category dependency executes before route body object resolution.
Readiness services also require an authorized actor and reject non-medical
actors before readiness source queries.

Technical system readiness remains available through the existing health and
configuration policy; it is not treated as patient clinical readiness.

### Scoped audit reference lookup

The audit reference resolver previously loaded an audit row globally and then
authorized it, creating different external results for absent and inaccessible
IDs. It now performs one query constrained by the caller's permitted clinic,
medical-institution and explicit system-security scopes. No result always uses
the same not-found response.

Denied lookups do not create a misleading `audit_log.viewed` event. Successful
lookups continue to record the exact allowed audit object through the existing
PHI-safe audit DTO.

## Regression mapping

| Finding | Regression evidence | Secure expectation |
| --- | --- | --- |
| `csf_97dc26c99e3af63d61794c8e` | `test_pr3_third_security_appointment_projection.py` and DB-backed sentinel scenarios | no free-text keys or sentinel values in operational API or DOM |
| `csf_a69f46f8e1f10d5afc8561c2` | `test_pr3_third_security_readiness.py`, route-registry tests and DB-backed persona scenarios | non-medical denial occurs before object lookup; scoped medical access remains available |
| `csf_fc0985796687b6ead948904a` | `test_pr3_third_security_audit_oracle.py` and PostgreSQL integration coverage | absent and inaccessible IDs have identical not-found behavior |

The three initial regression cases were executed against the unremediated
feature head and failed for the expected reasons before the fixes were applied.

## Sibling and variant disposition

| Family | Disposition | Reason |
| --- | --- | --- |
| Appointment operational routes | fixed | all routes now declare narrow operational/reception schemas |
| Web and API-key appointment intake | fixed | response contracts use the same narrow DTO |
| Package booking | safe | package scheduling uses identifiers and package projections, not broad patient notes |
| Clinical documents | safe | institution/clinic access uses existing scoped document policy and not-found semantics |
| Signed reports | safe | report reads use the existing medical and institution scope loaders |
| Episodes and clinical forms | safe | sensitive-access references use scoped journey/form queries |
| Invoices | safe | sensitive-access resolution queries invoice ID and active clinic together |
| API keys | not applicable | tenant-bound API-key management does not use audit-object reference resolution |
| Workflow tasks | safe | no sibling direct audit-ID lookup was found |
| Readiness snapshots and acknowledgments | fixed | all patient-clinical entry points now require canonical medical category |
| Appointment room/provider conflict validation | deferred, not equivalent | its conflict feedback is an operational scheduling rule, not a direct sensitive-object lookup |

## Performance evidence

Using the same synthetic appointment object:

- legacy broad appointment JSON: 1300 bytes;
- narrow operational appointment JSON: 691 bytes;
- reduction: 46.8%;
- two-row appointment list: 2 SQL statements, including authorization context;
- no additional lazy relationship query was introduced.

The clinical-readiness medical guard executes before route body and service
source resolution. The audit lookup remains anchored by the `AuditLog.id`
primary key and adds bounded scope predicates; no new index or migration is
justified.

## Executed local validation

Remediation implementation commits:

- `e022345` — remove free text from operational appointment projections;
- `8fd37c0` — require medical staff for clinical readiness;
- `ed62c08` — collapse inaccessible audit references to not-found;
- `c22dd03` — add browser and PostgreSQL regression coverage;
- `6b5bfc2` — measure projection payload and query behavior.

| Gate | Result |
| --- | --- |
| Python compilation | passed |
| Dedicated third-rescan regression modules | 15 passed |
| Fast backend gate | 149 passed |
| Process-isolated backend core shard A | 267 passed |
| Process-isolated backend core shard B | 552 passed, 2 skipped |
| PostgreSQL integration suite, including audit-oracle proof | 21 passed |
| Operational projection targeted suite | 5 passed |
| Readiness preview/registry targeted suite | 32 passed |
| Readiness snapshot/acknowledgment targeted suite | 90 passed |
| Audit targeted suite | 20 passed |
| Frontend contract tests | 4 passed |
| Frontend Vitest | 57 passed |
| Frontend typecheck, smoke and production build | passed |
| Route-mocked Playwright | 1 passed |
| Isolated DB-backed Playwright | 14 passed |
| Generated OpenAPI types check | passed |
| Development Compose config | passed |
| Production-example Compose config | passed with explicit synthetic overrides |

The final aggregate rerun, GitHub CI and post-merge security rescan are recorded
after they run; older green results are not reused for a later SHA.

## Migration evidence

- one Alembic head: `0067_audit_aggregation`;
- empty PostgreSQL database to head: passed;
- `0067 -> 0066 -> 0067`: passed;
- no migration was added because all three changes are response, authorization
  and query-scope changes;
- `alembic check` continues to report the repository's documented historical
  metadata drift. No new model/schema difference was introduced by this
  remediation, and no broad autogenerated migration was created.

## Boundaries and remaining gates

- `main` is unchanged.
- PR #7 remains Draft.
- recovery PR #4 is unchanged.
- PR #3 remains Draft and is not merged by this remediation.
- human usability has not been performed.
- production and real patient data are not authorized.
- Clinical Document Engine work has not started.
- GitHub CI must pass on the final remediation SHA.
- A read-only remediation review must return `APPROVED — REMEDIATION COMPLETE`.
- After merge into `feature/full-stack-production-validation`, a new full
  `main...feature/full-stack-production-validation` Codex Security scan must be
  completed and sealed.
