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
