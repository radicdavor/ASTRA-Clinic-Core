# PR #3 Security Review Remediation

## Increment A — baseline and route map

This document records the remediation of four merge-blocking findings from the independent review of PR #3. The findings are intentionally represented by strict expected-failure regression tests until the corresponding increment removes the defect.

| Finding | Root cause | Exposed paths | Baseline regression |
| --- | --- | --- | --- |
| P1 unresolved clinical documents | Institution list scope treats `clinic_id IS NULL` as a wildcard | clinical document list, search, patient list, detail, source download, evidence-derived routes | `test_unresolved_document_is_hidden_from_all_standard_clinical_read_paths` |
| P1 browser deployment contract | Production example separates frontend and API sites while frontend reads the API CSRF cookie | browser login, session bootstrap, every cookie-authenticated mutation, logout | `test_production_example_uses_one_same_origin_browser_auth_contract` |
| P2 CSRF session binding | Middleware compares only header and readable cookie | all unsafe browser-cookie requests | `test_csrf_token_from_another_session_is_rejected` |
| P2 durable invalid-session audit | Audit is added to the request transaction immediately before an HTTP exception | `get_current_user`, `get_current_actor`, session endpoint | `test_invalid_browser_session_audit_survives_unauthorized_response` |

### Canonical invariants

- A clinical document is institution-readable only when immutable document provenance explicitly identifies that institution.
- Patient associations do not establish document ownership.
- Unresolved legacy documents are excluded from all ordinary clinical read paths without existence disclosure.
- Production browser authentication uses one public origin with the API exposed below `/api`.
- Every unsafe browser request validates a CSRF token against the exact active `UserSession`.
- Invalid-session security audit uses a short transaction independent of the rejected request.

### Current route ownership map

| Route family | Canonical loader or policy | Returned content |
| --- | --- | --- |
| `/api/clinical-documents`, `/search`, patient document list | `institution_scoped_clinical_documents_statement` | full clinical document DTO |
| document detail, evidence timeline, OCR/review operations | `get_institution_scoped_clinical_document_for_read` | full document or derived evidence |
| `/api/clinical-documents/{id}/source` | scoped document loader plus download permission | original source bytes |
| patient clinical record | institution-scoped clinical-record projection | metadata-only timeline projection |
| unsafe browser requests | CSRF middleware in `app.main` | mutation response |
| browser/API authentication | `get_current_user` and `get_current_actor` | resolved user or actor |

PR #4 remains stacked and untouched. Its recovery hash projections and migration fixtures will require review after this remediation is integrated into PR #3.

## Increment B — canonical clinical-document institution provenance

`ClinicalDocument.institution_id` is now the sole normal-read tenant boundary. It is an indexed, nullable legacy-resolution foreign key to `Institution`; null means unresolved and is denied by every ordinary institution-scoped loader. Neither global patient identity nor patient-clinic associations participate in document ownership.

Migration `0063_clinical_document_institution_provenance` derives provenance only from immutable document links: the document clinic, originating appointment clinic, or originating journey clinic. It backfills a row only when all available candidates identify exactly one institution. Missing and conflicting candidates remain unresolved. Empty-database upgrade, `0063 -> 0062` downgrade, and re-upgrade pass on PostgreSQL. The repository's already-documented historical Alembic metadata drift remains; the new field itself adds no drift operation.

All application write paths now persist provenance explicitly:

- manual clinical-document creation and placeholder upload derive it from the validated clinic;
- journey source ingestion derives it from the journey clinic;
- signed-report generation derives it from the activity/journey clinic;
- demo records receive the demo gastro clinic provenance.

The scoped list, search, patient list, patient clinical-record metadata, detail, evidence, classification, and source-download paths now converge on the canonical institution value. The former `clinic_id IS NULL` wildcard and patient-association fallback were removed. Addenda inherit the exact original document institution.

## Increment C — same-origin production browser authentication

The sole recommended production browser topology is one HTTPS public origin. The gateway serves React at `/` and proxies `/api/*`, `/auth/*`, `/health`, and `/ready` to the private FastAPI service. The frontend defaults to `window.location.origin`; the production example leaves `VITE_API_BASE_URL` empty and does not publicly expose the backend port.

`BROWSER_PUBLIC_ORIGIN` is now an explicit production setting. Production startup rejects missing/non-HTTPS values and rejects a CORS origin list that differs from that canonical origin. Session and readable CSRF cookies remain host-scoped, `Secure`, and `SameSite=Lax`, which is coherent because frontend and API share an origin. The Nginx contract forwards original host/protocol and request ID, prevents auth response caching, and bounds document uploads.

## Increment D — session-bound CSRF validation

Login generates an independent random CSRF token and stores only its SHA-256 hash on the new `UserSession`. For every unsafe cookie-authenticated request, the normal authentication dependency resolves the active, non-expired, non-revoked session once and validates both the header token and readable same-origin cookie against that exact session hash. Hash comparison uses `hmac.compare_digest`; middleware performs the independent Origin/Referer check, while the session-aware dependency is the single authority for CSRF token validation.

Safe methods do not require CSRF. Browser login is exempt because no session exists yet. Logout validates the header against the resolved session before revocation, while Bearer and API-key requests remain outside the browser-cookie CSRF path. `/auth/session` rejects a readable CSRF cookie that does not belong to its active session instead of reflecting an arbitrary value. Raw session and CSRF material is never placed in audit or application logs.

## Increment E — durable browser-session security audit

Rejected browser-session and CSRF requests now write sanitized security metadata through a short SQLAlchemy transaction created independently of the request session. The writer commits only the audit row, closes its own session, and never receives a raw session token, CSRF token, authorization header, request body, or clinical data. Known sessions contribute only database identifiers and a bounded reason code; unknown and malformed tokens are classified without persistence of their value.

Covered events include revoked, expired, unknown, malformed, and inactive-user sessions; invalid CSRF for an active session; cookie/Bearer or cookie/API-key credential conflicts; successful logout; and revoke-all. Each rejected attempt intentionally produces one event—there is no lossy deduplication—while database-generated audit IDs make concurrent inserts independent.

If the audit transaction fails, the authentication decision remains fail-closed: the request is still rejected. The operational logger records only the correlation ID and action plus the sanitized database exception; it does not recursively audit the audit failure. PostgreSQL regression coverage proves that the audit commit survives the rejected request and does not commit a flushed business mutation in the request transaction.

## Increment F — repository-wide document access audit

The follow-up audit found and closed four indirect paths that did not use the canonical provenance boundary: processing-job metadata and execution, patient knowledge summaries, journey timeline/AI summary sources, and pathology result linking. Journey document ingestion is now also bound to the active clinic, and client-emitted sensitive-access audit events resolve documents by institution rather than by a nullable clinic or journey fallback.

| Route or consumer | Loader / policy | Scope and returned content | Access audit |
| --- | --- | --- | --- |
| clinical document list/search/patient list | `institution_scoped_clinical_documents_statement` | canonical institution plus confirmed clinical classification; full DTO | detail/source reads audited separately |
| detail, evidence timeline, addenda | `get_institution_scoped_clinical_document_for_read` or `ensure_institution_clinical_read` | canonical institution; full document or derived audit evidence | deduplicated read action |
| source download | provenance check before classification branch, then clinical/read-review policy | exact source bytes; foreign and unresolved both return 404 | source view action |
| OCR/classification queue, processing and job list | `get_document_for_classification_review` before every job lookup | canonical institution; job metadata only | mutation actions |
| patient clinical summary and draft sources | institution-scoped clinical statement plus source-ID subset validation | derived source-linked knowledge only | existing summary mutation audit |
| journey timeline and AI summary | active-clinic journey loader plus institution-provenance document statement | visit events and source-linked document projection | existing journey/summary actions |
| readiness preview | appointment clinic → institution filter | reviewed source-derived warnings only | immutable snapshot audit where requested |
| pathology result link | actor institution read plus case-journey institution equality | link metadata, never free cross-patient/institution attachment | pathology link action |
| sensitive-access event API | active clinic → institution equality | event receipt only; no clinical content | the event itself |
| demo seed | internal idempotent seed lookup | synthetic startup data only; not an API read path | not applicable |

No `ClinicalDocument.clinic_id IS NULL` wildcard remains. Unresolved documents are excluded from standard list, search, summary, timeline, processing-job, source, count, and client audit paths. Unauthorized document IDs use the existing not-found response to avoid cross-institution existence disclosure. Operational readiness may aggregate counts across all *resolved* active institutions for system readiness, but never includes unresolved documents or document content.

## Required CI regression gate

The backend CI job runs a named security gate immediately after the PostgreSQL
empty-upgrade, one-step downgrade, and re-upgrade check. The gate directly
exercises the four review findings and the indirect processing-job boundary:

- same-origin production browser configuration;
- CSRF rejection when a token is swapped between active sessions;
- durable rejected-session audit and isolation from the request transaction;
- denial of unresolved clinical documents through normal and processing paths.

PR #4 remains outside this remediation branch. It must not be retargeted or
merged until this stacked draft PR is independently reviewed and PR #3 is
revalidated.
