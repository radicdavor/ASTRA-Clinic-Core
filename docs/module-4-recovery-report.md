# Module 4 recovery validation report

Date: 22 July 2026

Scope: local and CI synthetic PostgreSQL 16 recovery. No real patient data,
production deployment, custom encryption, HA or live provider integration.

## Implemented

- PostgreSQL custom-format backup and restore using official version-pinned
  tools;
- atomic backup publication and explicit overwrite control;
- strict PHI-free main and file manifests with SHA-256;
- complete reconciliation of DB-referenced source objects;
- new/empty target protection;
- recovery-incomplete readiness marker;
- recognized Alembic revision validation and explicit old-revision upgrade;
- restored active-session revocation;
- bounded session cleanup CLI with dry-run, retention, batch and maximum limits;
- durable Compose document-storage volume and one-shot recovery image;
- structured operation IDs and redaction tests;
- dedicated CI recovery layer.

## Synthetic recovery evidence

The current-revision scenario created two institutions, three clinics, role and
membership boundaries, globally associated patients, appointments, journeys,
activities, an immutable signed report, exact-version addendum, clinical,
financial and unclassified source objects, invoices/payments, audit state and
active/revoked/expired sessions.

Observed result:

- revision `0062_signed_report_addendum_integrity` restored;
- 3 source objects restored with exact size/path/SHA-256 and classification;
- one active session revoked; old cookie rejected;
- 14 selected domain table projections matched pre-backup hashes;
- non-empty target rejected before marker creation;
- simulated interrupted restore failed non-zero and retained the not-ready
  marker;
- 11 application/security smoke checks passed, including health, ready, login,
  dashboard, clinical record, signed report, source download, billing and
  cross-institution denial.

The older-revision scenario restored
`0061_institution_model_clinical_record`, explicitly upgraded it to
`0062_signed_report_addendum_integrity` and passed revision/readiness checks.

Helper and failure coverage verifies secret/unknown manifest fields, unsafe
paths, corrupt dump, corrupt/missing/extra storage, absent manifest, duplicate
objects, unknown future revision, structured-log redaction and recovery marker
readiness behavior.

## Safety conclusions

Signed snapshots, exact addendum version links, source classification and file
hashes, patient/clinic associations, scheduling, billing, payments and audit
state are preserved by the tested flow. Backup artifacts are not committed and
temporary synthetic databases/storage are deleted.

## Remaining operational work

- select and enforce production RPO/RTO;
- provision platform-managed encryption and restricted off-site retention;
- test recovery on the selected Google Cloud deployment architecture;
- audit backup access and key management;
- add HA only if required and measured;
- retain the documented historical Alembic metadata-drift strategy;
- do not treat the untouched local 0061 development database as synthetic.

Decision: `MODULE 4 COMPLETE — READY FOR STACKED DRAFT PR` within the authorized
synthetic/local and CI validation scope. This is not production deployment
approval.
