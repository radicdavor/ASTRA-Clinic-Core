# Institution clinical access security matrix

Module 3 separates patient identity, clinical read, clinical write, operations and billing.

| Resource/action | Medical same institution | Admin same institution | Medical other institution | Author rule | Clinic scope | Permission | Test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical document detail | Allow when classified clinical | Deny | Deny/404 | No edit implied | Institution | `clinical.documents.read_institution` + medical category | `test_physician_and_nurse_read_clinical_documents_across_clinics_same_institution`, `test_administrative_and_other_institution_users_cannot_read_full_clinical_document` |
| Clinical record timeline | Metadata only | Deny | Deny/404 | Action flags only | Institution | `clinical.documents.read_institution` + medical category | `test_patient_clinical_record_lists_metadata_without_full_document_content`, `test_patient_clinical_record_denies_admin_and_other_institution` |
| Draft read | Allow if clinical and same institution | Deny | Deny/404 | Read is not edit | Institution | `clinical.documents.read_institution` + medical category | `test_author_controlled_draft_editing_and_signed_immutability` |
| Draft edit | Own draft only | Deny | Deny | `author_user_id == actor.user_id` | Institution for read, author for write | `clinical.documents.edit_own_draft` | `test_author_controlled_draft_editing_and_signed_immutability` |
| Signed edit | Deny | Deny | Deny | None | N/A | N/A | `test_author_controlled_draft_editing_and_signed_immutability` |
| Addendum | Allow when permitted and original signed/final | Deny | Deny/404 | Addendum author recorded | Institution | `clinical.documents.add_addendum` | `test_addendum_is_separate_audited_record_and_does_not_change_original` |
| Clinical source preview/download | Allow when source classification is clinical | Deny unless also medical and permitted | Deny/404 | No write | Institution | `documents.view_source` plus institution clinical read | `test_unclassified_and_financial_source_documents_are_not_institution_readable`, `test_document_ingestion.py` source path tests |
| Administrative source | Deny by classification | Deny | Deny | N/A | Clinic/future workflow | Explicit future policy required | `test_unclassified_and_financial_source_documents_are_not_institution_readable` |
| Financial source | Deny by classification | Deny | Deny | N/A | Billing clinic | Billing permissions only | `test_unclassified_and_financial_source_documents_are_not_institution_readable` |
| Billing/invoices | No implicit access from clinical read | Clinic billing only | Deny | N/A | Clinic | `billing.read` / `billing.write` | `test_institution_read_is_audited_and_does_not_open_finance_or_dashboard` |
| Appointment availability | Minimal scheduling conflict metadata | Allow per scheduling permission | Minimal only | N/A | Patient identity for overlap safety | `appointments.patient_availability.read` | `test_patient_appointment_availability_remains_minimal` |
| Journey/check-in/dashboard | No implicit access from clinical read | Clinic operations only | Deny | N/A | Clinic | `journey.*`, `checkin.*`, dashboard role permissions | `test_institution_read_is_audited_and_does_not_open_finance_or_dashboard` |
| Audit | Backend-derived metadata only | Per audit permission | Scope enforced by route | N/A | Entity/institution context | route permission | `test_institution_read_is_audited_and_does_not_open_finance_or_dashboard` |

Non-negotiable rule: `medical_staff` without permission is insufficient, and permission without `medical_staff` is insufficient.
