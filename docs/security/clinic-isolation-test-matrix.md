# Clinic isolation and institution clinical-read test matrix

## Model

ASTRA separates three authorization scopes:

1. **Institution-wide medical read**
   - clinical documents
   - signed reports
   - clinical forms where exposed as clinical record
   - relevant source documents
   - clinical history

2. **Author/delegated write**
   - own clinical drafts
   - controlled addenda
   - signing through explicit permission

3. **Clinic-local operations**
   - appointments
   - daily dashboard
   - check-in
   - rooms
   - materials
   - billing
   - payments
   - clinic administration

## Required guarantees

| Scenario | Expected result | Current regression coverage |
| --- | --- | --- |
| Physician Clinic A reads clinical document from Clinic B, same institution | `200` | `test_physician_and_nurse_read_clinical_documents_across_clinics_same_institution` |
| Nurse Clinic A reads physician report from Clinic B, same institution | `200` | `test_physician_and_nurse_read_clinical_documents_across_clinics_same_institution` |
| Nurse reads nursing documentation from another same-institution clinic | `200` | `test_physician_and_nurse_read_clinical_documents_across_clinics_same_institution` |
| Administrative user has `system.admin` but is not medical staff | clinical document denied | `test_administrative_and_other_institution_users_cannot_read_full_clinical_document` |
| Physician from another institution reads clinical document | safe denial (`404`) | `test_administrative_and_other_institution_users_cannot_read_full_clinical_document` |
| Nurse from another institution reads clinical document | safe denial (`404`) | `test_administrative_and_other_institution_users_cannot_read_full_clinical_document` |
| Same-institution non-author edits another clinician's draft | `403` | `test_author_controlled_draft_editing_and_signed_immutability` |
| Nurse edits physician draft | `403` | `test_author_controlled_draft_editing_and_signed_immutability` |
| Physician edits own draft | `200` | `test_author_controlled_draft_editing_and_signed_immutability` |
| Nurse edits own nursing documentation draft | `200` | `test_author_controlled_draft_editing_and_signed_immutability` |
| Signed document is standard-patched | `409` | `test_author_controlled_draft_editing_and_signed_immutability` |
| Addendum is created | separate object; original unchanged | `test_addendum_is_separate_audited_record_and_does_not_change_original` |
| Institution clinical read occurs | audit event recorded | `test_institution_read_is_audited_and_does_not_open_finance_or_dashboard` |
| Medical read permission attempts finance list | denied without finance permission | `test_institution_read_is_audited_and_does_not_open_finance_or_dashboard` |
| Medical read permission attempts dashboard | denied without operational permission and clinic scope | `test_institution_read_is_audited_and_does_not_open_finance_or_dashboard` |
| Non-clinical source document is opened through clinical-read path | denied | `test_administrative_and_other_institution_users_cannot_read_full_clinical_document` |
| Patient appointment availability | minimal scheduling data only | `test_patient_appointment_availability_remains_minimal` |

## Non-goals

- No break-glass PHI access was introduced.
- No financial, HR, commercial, or system-admin data is included in institution-wide clinical read.
- No delegation workflow is implied by author-controlled write; unsupported delegated editing remains denied.
