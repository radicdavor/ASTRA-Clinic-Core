# Full-stack production validation status

## Module 3 focus

Institution-aware clinical record access is implemented incrementally on `feature/full-stack-production-validation`.

Implemented in the current increment:

- `Institution` model;
- `Clinic.institution_id`;
- medical professional category checks;
- institution-wide clinical-document read policy;
- author-controlled draft editing for canonical `ClinicalDocument`, including immediate permission revocation behavior;
- signed/final document addenda and report-scoped addenda with a direct exact-report FK;
- signed-report snapshot integrity and API-level immutability checks;
- metadata-first patient clinical record endpoint;
- restrictive source-document classification policy for institution read/download;
- human source classification endpoint for the one-way `unclassified` review transition;
- metadata-only classification audit payloads;
- frontend clinical-document classification and separately listed addendum UI;
- security matrix and ADR documentation.

Validated in this increment:

- backend compileall and the full isolated-PostgreSQL suite: 681 tests, exit code 0;
- focused institution, ingestion and signed-report tests: 36 passed;
- focused PostgreSQL integration and pilot flow: 7 passed;
- Alembic single head `0062_signed_report_addendum_integrity`;
- empty PostgreSQL upgrade to head, downgrade to `0060`, and re-upgrade to head;
- exact signed-report foreign-key presence after migration;
- generated OpenAPI contract drift check;
- frontend typecheck, 54 Vitest tests and 4 contract tests;
- frontend smoke and production build;
- route-mocked Playwright: 1 passed;
- isolated DB-backed Playwright: 10 passed;
- development and production-example Docker Compose configuration validation.

## PR #3 security-review remediation

The follow-up hardening branch adds migration
`0063_clinical_document_institution_provenance` and closes four independent
review findings: unresolved clinical-document ownership, a split-origin browser
deployment contract, CSRF tokens reusable across sessions, and rejected-session
audit rows lost with the request transaction. A repository-wide document read
audit also brings processing jobs, patient summaries, journey timelines,
readiness projections, pathology linking, ingestion, source download, and
client-emitted sensitive-access events under the same provenance boundary.

The CI backend job now executes a named PR #3 security regression gate after an
empty PostgreSQL upgrade/downgrade/re-upgrade. It covers same-origin production
configuration, cross-session CSRF rejection, durable invalid-session audit,
transaction isolation of the audit writer, and denial of unresolved document
and processing-job paths. Full validation results are recorded in
`pr3-security-review-remediation.md`; counts in earlier module sections remain
historical results rather than being rewritten.

The remaining local warning is the existing third-party `python-jose` use of
`datetime.utcnow()`; it does not fail the suite and is not introduced by this
increment.

PR #5 has been integrated into PR #3's feature branch with its reviewed commit
history preserved. The integrated contract has one Alembic head, 0063, and
enforces same-origin browser authentication, session-bound CSRF, durable
invalid-session auditing, explicit clinical-document institution provenance,
and deny-by-default handling of unresolved legacy documents. PR #4 is not part
of this integration and requires a separate 0063 recovery update only after
PR #3 is merged into `main`.

Module 3 is closed for the authorized local/demo scope. Broader production validation remains separate from Module 3 functional closure.

## PR #3 scope and audit blocker remediation

The stacked remediation advances the single Alembic head to `0066` and closes
the active-clinic billing, institution clinical-child provenance, audit
projection, and API-key tenant-scope findings. Null or conflicting legacy
provenance is deny-by-default. The safe global `Patient` directory remains an
identity/deduplication surface and does not grant access to child records.

Local evidence at the remediation HEAD: 147 fast backend tests, 737 full
non-integration backend tests, 16 PostgreSQL integration tests, 57 frontend
tests plus 4 contract tests, 1 route-mocked Playwright scenario, 11 DB-backed
Playwright scenarios including explicit foreign clinical-derived-data denial,
OpenAPI drift check, and empty/populated migration cycles
passed. See `pr3-scope-and-audit-remediation.md` for the scope matrix and the
mandatory separate PR #4 recovery update plan.

## Module 3.5 Lean Core validation

Lean Core optimization is complete in the local synthetic scope. It retains the
three-process production model, centralizes clinical/institution authorization,
reduces guarded SQL counts, returns metadata-only clinical-record lists, cuts
entry JavaScript from 239,861 B to 63,861 B, and reduces initial journey
workspace requests from 16 to 9 (documents) or 8 (encounter).

Final gates: 687 backend tests passed with one POSIX-only Windows skip, 16
PostgreSQL integration tests passed, 57 frontend and 4 contract tests passed,
route-mocked Playwright passed, all 10 DB-backed Playwright scenarios passed,
OpenAPI passed, and empty upgrade/downgrade/re-upgrade passed. Production and
development Compose models parse. The optional Alembic metadata drift check and
the variable late-run endpoint latency sample are documented limitations, not
silently treated as successes. See `lean-core-optimization.md`.
