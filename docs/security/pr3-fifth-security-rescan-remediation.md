# PR #3 Fifth Security Rescan Remediation

## Scan and finding

- Scanned revision: `f89ac29475cb2cb26d25d7d44fd3a2c5fa2405f4`
- Sealed scan ID: `f89ac29_20260726T091535Z`
- Diff coverage: `123/123`
- Reportable finding: `1 Medium / P2`, high confidence
- Finding ID: `csf_b735f2ff381f275e4c5edb0a`

The document parent was correctly constrained to the reader's institution.
The defect occurred after authorization: `ClinicalDocumentOut` embedded the
broad global `PatientOut`, which included the free-text `Patient.notes` field
and unrelated patient fields.

## Affected surface

The four reported read surfaces were:

- clinical-document list;
- clinical-document search;
- clinical-document detail;
- clinical documents for a selected patient.

Create, upload, update, extraction and review routes use the same response
model and therefore inherit the same corrected contract. The complete producer
inventory is in
`docs/security/pr3-fifth-security-rescan-surface.md`.

## Remediation

`ClinicalDocumentOut.patient` now uses
`ClinicalDocumentPatientIdentityOut`, with this exact allowlist:

- `id`;
- `first_name`;
- `last_name`;
- `date_of_birth`.

The nested schema contains no notes, contact details, OIB, timestamps or other
free text. Response shape does not vary by role and no runtime dictionary
redaction is used. The document list query retains joined loading but selects
only the four approved patient columns.

Document institution scoping, medical-category enforcement, classification
review, signed-report integrity and patient storage models are unchanged. No
database migration was required.

## Regression evidence

The four HTTP surfaces are parameterized against a shared-patient scenario
with same- and foreign-institution documents. Tests assert both the absence of
synthetic note sentinels and equality with the exact patient-field allowlist.
Schema/OpenAPI introspection prevents a future return to `PatientOut`.

The query regression confirms one joined clinical-document/patient select,
excludes the patient `notes` column and bounds the request to four SQL
statements including authorization context.

The isolated DB-backed browser test exercises all four responses and verifies
that three synthetic note sentinels are absent from the network payload and
the document list/detail DOM. Foreign-institution document access remains
not-found and non-medical access remains denied.

## Performance

A representative nested patient payload decreased from `269` bytes with the
broad schema to `87` bytes with the identity allowlist: `182` bytes, or `67.7%`,
less per returned document. List and detail use the same nested projection.
The list continues to use one joined data query and introduces no lazy-load or
N+1 regression.

## Local validation

Measured on the remediation branch:

| Gate | Result |
| --- | --- |
| Python compileall | passed |
| Dedicated four-endpoint/schema/query regressions | `6 passed` |
| Clinical-document access suite | `28 passed` |
| Clinical-document behavior suite | `49 passed` |
| Route registry | `2 passed` |
| Backend fast gate | `149 passed` |
| Full backend isolated shard A | `273 passed` |
| Full backend isolated shard B | `557 passed, 2 skipped` |
| PostgreSQL integration | `22 passed` |
| PR #3 security gate plus fifth-rescan tests | `64 passed, 1 skipped` |
| Frontend Vitest | `57 passed` |
| Program 2 contract tests | `4 passed` |
| Frontend typecheck, smoke and production build | passed |
| Route-mocked Playwright | `1 passed` |
| Isolated DB-backed Playwright | `15 passed` |
| OpenAPI generation and drift check | passed |
| Development and production-example Compose config | passed with synthetic values |

Migration evidence:

- one head: `0068_document_classification_default`;
- empty PostgreSQL database to head: passed;
- `0068 -> 0067 -> 0068`: passed;
- no migration was added by this response-contract remediation.

Implementation commits:

- `1e63484` — narrow the nested patient identity;
- `3537a3f` — update generated and frontend contracts;
- `a1178de` — add DB-backed sentinel coverage;
- `9874e99` — verify query columns and count.

## Remaining gates

At this documentation revision, push, current-SHA GitHub CI, read-only review,
merge into `feature/full-stack-production-validation` and the required new
full sealed Codex Security rescan are still pending.

PR #3 remains Draft. `main`, PR #4 and PR #7 are unchanged. Human usability
has not been performed. Production and real patient data are not authorized.
Clinical Document Engine work has not started.
