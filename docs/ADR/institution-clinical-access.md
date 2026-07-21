# ADR: Institution-aware clinical access

## Status

Accepted for Module 3 incremental implementation.

## Decision

Patient identity is global inside one ASTRA installation. Clinical read access is institution-wide only for explicitly authorized medical staff. Clinic operations, clinic dashboards, scheduling actions, billing, invoices and payments remain clinic-scoped.

The implemented path is:

```text
User -> active ClinicMembership -> Clinic -> Institution
ClinicalDocument -> Clinic -> Institution
```

Institution-wide clinical read requires all of:

1. authenticated active user;
2. role `professional_category = medical_staff`;
3. permission `clinical.documents.read_institution`;
4. active clinic membership in the same institution as the document;
5. document marked `is_clinical_record = true`;
6. document `record_classification = clinical`.

Administrative staff, billing staff and system administrators do not receive PHI access merely because they are privileged users. System administration is not a break-glass clinical access path.

## Write model

Institution read is not institution edit.

Draft editing is author-controlled:

```text
ClinicalDocument.review_status != signed
AND ClinicalDocument.author_user_id == current_user.id
AND clinical.documents.edit_own_draft
```

Signed clinical documents are immutable through standard update paths. Corrections are recorded as separate addenda. Addenda preserve original document identity, patient, clinic, institution, author, signing user and timestamp. The original content is not overwritten.

## Source document classification

`ClinicalDocument.record_classification` separates institution-readable clinical source documents from administrative, financial, private internal and unclassified material.

Only `clinical` is institution-readable in Module 3. Legacy/unknown source material should be treated restrictively unless explicitly classified by a trusted backend workflow.

## Timeline/list response rule

`GET /api/patients/{patient_id}/clinical-record` returns metadata only:

- document ID;
- patient ID;
- date;
- clinic;
- document type;
- title;
- author snapshot;
- status;
- addendum count;
- allowed user actions.

It does not return full raw text, rendered report content or AI summary content.

## Boundaries

Allowed:

- physician/nurse same institution reads clinical documents across clinics;
- author edits own draft;
- authorized medical staff adds an addendum to a signed/final clinical document;
- source file download after institution clinical read and source classification check.

Denied:

- cross-institution read;
- administrative clinical read;
- billing access by clinical read permission;
- operations/dashboard access by clinical read permission;
- signed document overwrite;
- client self-promotion of source classification.
