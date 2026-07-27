# Module 3 — Institution Clinical Record Security Matrix

Module 3 protects one shared clinical record inside an institution while keeping operations, billing and non-clinical source material scoped separately.

| Capability | Allowed | Denied | Enforcement | Coverage |
| --- | --- | --- | --- | --- |
| Institution clinical document read | Medical staff with `clinical.documents.read_institution` in the same institution | Administrative staff, other institutions, non-clinical source classifications | `ensure_institution_clinical_read` checks professional category, permission, institution and `record_classification="clinical"` | `test_institution_clinical_document_access.py`, PG integration scenario |
| Draft/document editing | Author only, with `clinical.documents.edit_own_draft`; existing review workflow statuses remain editable when author-owned or legacy-reviewed | Other clinicians, nurses editing another author, administrative staff, foreign institution, signed documents | `get_authored_draft_for_edit` / `can_edit_clinical_draft` | `test_author_controlled_draft_editing_and_signed_immutability`, permission revocation test |
| Legacy unknown-author drafts | Read-only if otherwise clinical and institution-readable | Standard edit path | Author requirement for `draft` without `author_user_id` | `test_foreign_drafts_are_readable_but_not_editable_and_legacy_unknown_author_is_read_only` |
| Signed clinical document edit | Never through standard patch | All users | Structured `signed_document_immutable` conflict | signed-document tests |
| Signed report mutation | No API mutation; PostgreSQL trigger blocks direct update/delete where PG is active | Update/delete of signed report content/hash rows | `content_hash`, `verify_report_integrity`, DB immutability trigger | `test_signed_reports.py`, PG quality-gate trigger test |
| Signed report addendum | Separate signed addendum on the generated source document after report integrity verification | Addendum when report hash is invalid | `/api/signed-reports/{id}/addenda` + `create_document_addendum` | `test_signed_report_addendum_*` |
| Source-document ingestion | Source is preserved and starts as `unclassified` | Automatic entry into clinical record | `ingest_source_document` sets `record_classification="unclassified"` | `test_document_ingestion.py` |
| Human source classification | Reviewer in same institution may classify as `clinical`, `administrative`, `financial` or `unclassified` | Cross-institution review, ordinary source viewing of unclassified material | `/api/clinical-documents/{id}/classification/review` | classification review tests |
| Clinical source download | Medical clinical read for `clinical`; reviewer-only access for unclassified classification work | Admin-only, financial/admin source as clinical record | source route branches by classification | source download tests |
| Clinical record UI | Displays classification, review state, source contribution, addendum form | Autonomous clinical interpretation | Existing Clinical Documents UI | frontend typecheck/tests/build |

Non-negotiable boundaries:

- patient identity is global for matching and scheduling safety;
- clinical read is institution-wide only for authorized medical staff;
- billing and operations are not opened by clinical-read permission;
- source classification is human-controlled;
- signed reports are immutable snapshots;
- addenda never rewrite the original.

