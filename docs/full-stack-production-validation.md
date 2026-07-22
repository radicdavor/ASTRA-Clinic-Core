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

The remaining local warning is the existing third-party `python-jose` use of
`datetime.utcnow()`; it does not fail the suite and is not introduced by this
increment.

Module 3 is closed for the authorized local/demo scope. Broader production validation remains separate from Module 3 functional closure.

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
