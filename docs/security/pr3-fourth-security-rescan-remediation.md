# PR #3 Fourth Full Security Rescan Remediation

## Scan and scope

- Sealed scan ID: `acc67932_20260726T055110Z`
- Scanned PR #3 revision: `acc6793223e27e7f1a69d79d3e9cf26ce3c11997`
- Diff scope: `main...feature/full-stack-production-validation`
- Coverage: `120/120`
- Reportable findings: `2 Medium`, `1 Low`
- Previously remediated findings not reproduced: `11`
- Hardening decision: proportional local fixes; no new architecture

PR #3 remains a synthetic/demo validation branch. This remediation does not
authorize production use, real patient data, human usability claims, or the
Clinical Document Engine.

## Root causes and affected surfaces

| Finding | Root cause | Affected surface |
| --- | --- | --- |
| Journey response exposed patient free text | `JourneyOut` embedded a broad patient schema containing `notes` | patient-journey detail and consumers of that contract |
| Global search exposed raw ORM rows | `/api/search` returned ORM entities without an explicit response model | patient, appointment and service search groups |
| Manual documents defaulted to clinical | application and database defaults classified new documents as `clinical` before human review | manual clinical-document creation and direct ORM insertion |

The sibling review is recorded in
`docs/security/pr3-fourth-security-rescan-surface.md`.

## Implemented boundaries

### Narrow operational projections

- Patient-journey detail now uses the existing reception identity projection.
  It contains only the identity and concurrency fields needed by reception and
  never contains `notes`.
- Global search has a typed `SearchResponse` and explicit SQL column
  projections for patient, appointment and service results.
- Workflow task projections use purpose-built patient, episode and provider
  summaries and constrain ORM loading to their declared columns.
- Operational responses do not change shape by role. Clinical free text
  remains available only through separately authorized clinical or patient
  detail routes.

### Fail-closed document classification

- Manual document creation explicitly persists `unclassified`.
- The ORM and database server defaults for future rows are `unclassified`.
- Alembic revision `0068_document_classification_default` changes only the
  server default. It does not rewrite historical rows.
- Human-reviewed synthetic fixtures and signed-report generation declare
  `clinical` explicitly where their provenance is already trusted.

The original document remains the source of truth. `unclassified` documents
remain outside standard clinical read paths until an authorized reviewer
classifies them.

## Regression coverage

| Boundary | Test evidence |
| --- | --- |
| Journey and search omit free text | `test_pr3_fourth_security_operational_projections.py` |
| Manual and default documents are unclassified | `test_pr3_fourth_security_document_classification.py` |
| PostgreSQL server default is fail-closed | `test_pr3_fourth_security_rescan_pg.py` |
| Historical rows are not rewritten | `validate_0063_document_provenance.py` migration cycle |
| Browser/API sentinels stay absent | DB-backed `clinic-workflow.spec.ts` |

The DB-backed seed uses synthetic
`SECRET_PATIENT_NOTE_SENTINEL` and
`SECRET_APPOINTMENT_NOTE_SENTINEL` values. The test verifies their absence
from appointment, reception, search, patient-journey and browser output.

## Local validation

All figures below were measured on this remediation branch:

| Gate | Result |
| --- | --- |
| Python compileall | passed |
| Backend fast gate | `149 passed` |
| Backend full shard A | `267 passed` |
| Backend full shard B | `558 passed, 1 skipped` |
| PostgreSQL integration | `22 passed` |
| PR #3 security gate plus fourth-rescan tests | `63 passed, 1 skipped` |
| Frontend Vitest | `57 passed` |
| Program 2 contract tests | `4 passed` |
| Frontend typecheck, smoke and production build | passed |
| Route-mocked Playwright | `1 passed` |
| DB-backed Playwright | `14 passed` |
| OpenAPI generated-type check | passed |
| Development and production-example Compose config | passed with synthetic values |

Migration validation:

- one Alembic head: `0068_document_classification_default`;
- empty PostgreSQL database to `0068`: passed;
- `0068 -> 0067 -> 0068`: passed;
- populated `0062 -> 0068`: passed;
- historical document classifications remained unchanged.

The implementation commits before this documentation commit are:

- `d3eef38` — remove free text from operational projections;
- `8292f9d` — require review for manual document classification;
- `d530082` — make the trusted signed-report test fixture explicit;
- `24efcd9` — extend DB-backed sentinel coverage.

## Pending external gates

At the time of this document:

- Draft PR creation and current-SHA GitHub CI are pending;
- merge into `feature/full-stack-production-validation` is pending;
- the required new full sealed Codex Security scan is pending.

The remediation is not closed until those gates complete without reportable
Medium or High merge blockers.
