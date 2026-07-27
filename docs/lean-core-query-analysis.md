# Lean Core query analysis

Status: Module 3.5 Increment C

## Method

Measurements used a uniquely named PostgreSQL database migrated from empty to
Alembic head and the full-stack E2E synthetic seed. Browser-session
authentication and `X-Clinic-Id` were enabled. Counts include authorization,
membership and access-audit SQL so they describe the whole HTTP request.

The endpoint-specific budgets in `performance-budget.md` exclude shared auth
setup. In the measured browser flow, shared auth and active-clinic setup use six
statements for clinic-scoped requests. The current-session endpoint uses four
statements.

## Query counts

| Request | Before | After | Endpoint work after shared auth | Result |
| --- | ---: | ---: | ---: | --- |
| current browser session | 4 | 4 | 4 total | unchanged |
| daily dashboard | 12 | 11 | 5 | within 5–8 budget |
| patient directory | 8 | 7 | 1 | within budget |
| patient appointment availability | 9 | 8 | 2 | no N+1 observed |
| patient invoice/payment projection | 11 | 10 | 4 | no N+1 observed |
| institution clinical record | 16 | 11 | 4 after actor load | reduced 31% |
| signed report detail | 15 | 11 | report, source, scope and audit checks | reduced 27% |

The reductions come from loading each active membership and its clinic in one
query, resolving institution membership once per policy operation and reusing
that immutable scope for the read audit. No long-lived authorization cache was
added; permission and membership revocation still apply on the next request.

## Metadata projection

The clinical-record endpoint now has a dedicated metadata query. It loads only:

- identity and patient linkage;
- date and creation timestamp;
- clinic name;
- type, title and author metadata;
- review/signature metadata;
- author ID needed for capability projection.

`raw_text`, `ai_summary`, OCR text, attachment data and other full document
content are not selected. The count query uses `COUNT(clinical_documents.id)`
over the scoped relation rather than wrapping a full-entity subquery. A
regression test inspects executed SQL and fails if `raw_text` or `ai_summary`
returns to this metadata path.

## Readiness result

The readiness endpoint previously created and disposed a separate SQLAlchemy
engine and parsed the Alembic graph for every request. It now uses the existing
application pool and caches only the process-static Alembic script metadata.
The live database connection and current revision are still checked on every
request.

| `/ready`, 20 warm requests | Before | After |
| --- | ---: | ---: |
| median | 359.96 ms | 16.47 ms |
| p95 | 524.98 ms | 18.40 ms |
| maximum | 815.12 ms | 164.61 ms |

The p95 improvement is 96.5% and the endpoint now meets the 250 ms budget.

## Query plans and index decision

PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` was run only on an isolated synthetic
database containing 20,000 patients and 200,000 clinical documents.

Patient substring search used a sequential scan and returned its single match
in 33.97 ms. This is below the API budget and does not justify the operational
cost of `pg_trgm` or a search service at the stated capacity. The bounded
directory response remains limited to 50 rows.

Clinical-record metadata for a patient with ten records used
`ix_clinical_documents_patient_id`, read 12 shared buffers and completed in
0.35 ms. The ten-row sort used 26 KiB. A new composite index would not improve
this representative plan enough to justify additional write/storage cost.

Existing migrations already provide the critical clinic membership, patient
association, appointment clinic/date, journey clinic, clinical document
patient/classification, signed report, addendum and session indexes. Increment C
therefore adds no migration and no speculative index.

## Regression guards

The shared SQLAlchemy test helper records statements without enabling verbose
production SQL logging. Bounds cover:

- dashboard;
- patient directory;
- institution clinical record;
- signed report detail.

The full-stack measurement additionally records appointment availability,
invoice/payment projection and current session. Query budgets are deliberately
upper bounds, not assertions that every query is inherently desirable.
