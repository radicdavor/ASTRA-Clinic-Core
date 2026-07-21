# Production safety foundation

This branch keeps the production-safety foundation deliberately conservative.

Current security posture:

- patient identity can be global to avoid duplicate patient records;
- clinic operations remain scoped by active `ClinicMembership` and active clinic context;
- billing remains clinic-scoped;
- clinical read may span clinics only inside the same `Institution`;
- institution-wide clinical read requires both `professional_category = medical_staff` and `clinical.documents.read_institution`;
- source documents require explicit one-time human classification before institution-wide source preview/download; later reclassification is blocked;
- signed clinical documents are immutable through standard write paths;
- corrections use addenda rather than overwriting the original document, and signed-report addenda reference the exact signed report version;
- audit events are backend-derived and do not trust frontend-supplied institution or clinic metadata.

Module 3 migration assumption:

Existing local/synthetic clinics with the same `institution_key` are backfilled into a matching `Institution`. If no clinics exist, migration creates a default `ASTRA` institution for future clinic assignment. `Clinic.institution_key` remains compatibility metadata; `Clinic.institution_id` is the durable institution relation. Migration `0062` backfills a direct signed-report reference for existing report addenda while leaving generic clinical-document addenda nullable.

Not production-authorized in this increment:

- break-glass PHI access;
- cross-institution clinical sharing;
- live source-document integrations;
- real patient data entry;
- autonomous clinical decision-making.
