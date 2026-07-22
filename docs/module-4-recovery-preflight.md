# Module 4 recovery preflight

Date: 22 July 2026

Branch base: `0b10e99` (`feature/full-stack-production-validation`)

Scope: synthetic/local recovery engineering only; no production data or deployment.

## 1. PostgreSQL data inventory

PostgreSQL is authoritative for organization, identity, authorization,
scheduling, clinical metadata/content, billing and audit state. The current
0062 model contains 82 tables. Recovery must preserve at least these groups:

| Group | Canonical tables and relationships | Recovery requirement |
| --- | --- | --- |
| Organization and access | `institutions`, `clinics`, `users`, `roles`, `permissions`, `role_permissions`, `clinic_memberships`, `api_keys` | Preserve IDs, active state, Institution → Clinic and User → Membership. Secrets are not exported separately from their database hashes. |
| Sessions | `user_sessions` | Preserve rows for history if present, then revoke every active/non-expired row before the restored system can serve authenticated traffic. |
| Patient identity | `patients`, `patient_clinic_associations` | Preserve one global Patient identity and controlled clinic associations. |
| Scheduling and visit | `appointments`, `patient_journeys`, `journey_activities`, participants, preparations, forms, reminders, check-in, blockers, events and encounters | Preserve clinic, patient, appointment, activity and status links. |
| Clinical forms and reports | form definitions/versions/instances/revisions, `signed_clinical_reports`, `clinical_documents`, addenda, findings, questions, summaries and readiness snapshots | Preserve immutable signed content hash, exact report version/addendum links, authorship, classification and provenance. |
| Procedures/pathology | interventions, pathology cases/specimens/report links | Preserve activity and specimen provenance. |
| Inventory and billing | inventory, stock, suppliers, purchase orders, invoices, invoice lines and payment transactions | Preserve patient/journey provenance, amounts and payment allocations. |
| Configuration | services, rooms, packages, templates, modules, workflows and knowledge catalog | Required for application readiness after restore. |
| Audit | `audit_logs`, print and delivery events | Preserve actor/scope/object history; integrity checks must not require or emit raw clinical text in operational logs. |

The PostgreSQL custom-format dump is necessary but not sufficient because
uploaded source bytes live outside PostgreSQL.

## 2. File and object storage inventory

`DOCUMENT_STORAGE_PATH` defaults to `/app/data/documents`. On the current
Windows local host that resolves to `C:\app\data\documents`. Source ingestion
stores an opaque relative path (`journey-id/random-uuid.ext`) in
`clinical_documents.attachment_path`, while PostgreSQL holds MIME type, byte
size and SHA-256.

| Content | Location | Canonical | Regenerable | Backup/retention decision |
| --- | --- | --- | --- | --- |
| Uploaded/scanned source PDF, image, TIFF or text | `DOCUMENT_STORAGE_PATH/<attachment_path>` | Yes | No | Must be backed up with exact relative path, size and SHA-256 and reconciled to the DB document ID/classification. Retention follows the clinical source record. |
| Generated signed report | Structured data and rendered content in PostgreSQL | Yes | Rendering can be repeated, but the signed snapshot cannot be replaced | PostgreSQL dump is authoritative. Any future exported PDF is a derived artefact unless explicitly promoted to a source object. |
| OCR text/classification/AI summary | PostgreSQL derived columns/jobs | Derived but auditable | Provider-dependent | Preserve through DB backup; never substitute it for the source object. |
| Temporary upload/dump/work directory | operation-specific temporary directory | No | Yes | Exclude; delete on success and failure. |
| User exports | No canonical export repository currently exists | No | Usually | Exclude unless a future policy explicitly makes an export authoritative. |
| Remote object storage | Not implemented | N/A | N/A | A production object-store backup policy is required before moving storage off local disk. Do not invent a custom cloud engine. |

The inspected 0061 development DB has no `attachment_path` rows. The local
storage directory contains 402 small files (11,657 bytes total) that are not
referenced by that database. They may be old synthetic test artefacts; they are
not deleted or assumed disposable by this track.

The current production Compose example does not mount the document path as a
durable volume. Module 4 must add an explicit storage volume/mount before it can
claim a complete deployment backup boundary.

## 3. Secrets and configuration inventory

Database dumps, storage manifests and logs must not contain raw database URLs,
passwords, JWT/session secrets, cookie values, storage credentials or
encryption keys. These require a separate secrets-manager/configuration backup
procedure:

- PostgreSQL credentials;
- JWT/session secret and cookie security configuration;
- object-storage credentials when such storage exists;
- backup encryption/KMS keys;
- external provider credentials;
- deployment environment and DNS/TLS configuration.

Loss of the JWT secret invalidates token-based credentials but is not a reason
to preserve old browser sessions. Restored browser sessions are explicitly
revoked regardless of secret continuity.

## 4. Recovery invariants

The restore verifier must preserve:

```text
Institution → Clinic
User → ClinicMembership
Patient → PatientClinicAssociation
Appointment → Clinic/Patient
Journey → Appointment/Clinic
SignedReport → exact immutable version/hash
Addendum → exact signed report version
SourceDocument → classification/storage object/hash
Invoice → Journey/Patient
Payment → Invoice
AuditEvent → actor/scope/object
```

It must also prove cross-institution denial, author/signer provenance,
unclassified-document restriction, invoice/payment totals and that `/ready`
uses the restored Alembic revision.

## 5. Browser session decision

`user_sessions` may be restored to retain historical rows and audit links, but
every row that is active and not expired must receive `revoked_at` before the
restored application is exposed. Old cookies must fail. This prevents a copied
session bearer token from becoming valid again in a recovered environment and
creates an explicit security boundary between the failed and restored systems.

Session revocation is a required post-restore operation, separate from normal
expired/revoked-session retention cleanup. The existing cleanup command only
deletes already revoked, expired rows and therefore cannot satisfy this rule by
itself.

## 6. Alembic drift recovery relevance

The 86 top-level differences documented in `alembic-metadata-drift.md` are
classified for recovery as follows:

| Drift group | Recovery relevance | Decision |
| --- | --- | --- |
| Different index names/equivalent representations | Low | Benign metadata mismatch. Restore PostgreSQL objects exactly; do not autogenerate replacements. |
| Migration-owned operational indexes absent from ORM metadata | High for performance, not row integrity | Verify expected index names after restore. Never drop them from an autogenerated diff. |
| ORM convenience indexes absent from migrations | Low until a measured query needs one | Future migration only with query evidence. Not a restore blocker. |
| Unique constraint versus unique index representation | High semantic invariant | Verify actual PostgreSQL uniqueness, not ORM spelling. |
| DB-only uniqueness constraints | High semantic invariant | Verify names/columns after restore. Do not remove. |
| Historical timestamp nullability/defaults | Medium | Restore exact schema and values. Future tightening needs a data audit; not a restore blocker. |
| Legacy `journey_encounters.activity_id` | High for historical compatibility | Preserve until a dedicated retention/migration decision. |
| Redundant journey uniqueness representation | Medium | Verify uniqueness remains enforced. |

`alembic check` alone is not a recovery gate. The gate uses dump revision,
actual migration chain, required table/constraint/index inventory, data/file
integrity manifest and application/security smoke tests.

## 7. Local development database at 0061

Read-only inspection found:

- revision `0061_institution_model_clinical_record`;
- size 15 MB;
- 2 patient rows;
- no clinical documents or attachment links;
- no active sessions.

No patient fields or document contents were inspected. Synthetic provenance is
therefore not proven. Treat this database as potentially valuable and make it
the first practical backup candidate only after the tooling and checksum gate
are validated against isolated synthetic databases. Do not upgrade, dump into
Git, delete or use it as a Module 4 test source.

## 8. Backup completeness criteria

A backup is complete only when:

1. `pg_dump --format=custom` succeeds into a temporary artefact;
2. Alembic revision and PostgreSQL/tool versions are recorded;
3. every DB-referenced source object exists and matches DB size/SHA-256;
4. the storage archive contains no missing or extra canonical object;
5. dump, storage manifest/archive and overall manifest checksums are recorded;
6. manifest contains no PHI, filename, URL, token or credential;
7. artefacts are atomically published and existing artefacts are not silently overwritten.

## 9. Restore completeness criteria

A restore is complete only when:

1. checksums and manifest schema validate before mutation;
2. target database and storage are new/empty unless an explicit destructive test flag is supplied;
3. `pg_restore` succeeds and restored revision is recognized;
4. any explicit supported upgrade reaches the single current head;
5. DB/file integrity and recovery invariants match the pre-backup manifest;
6. all active sessions are revoked;
7. `/health`, `/ready`, login, clinic context, dashboard, clinical record, signed report/addendum, source access, billing and cross-institution denial pass;
8. partial failure leaves the target marked unusable and returns non-zero.

## 10. Blockers

There is no blocker to isolated synthetic implementation. Production readiness
remains blocked until:

- file storage is mounted durably and included in backup;
- platform-managed encryption, restricted access and off-site copy exist;
- retention, RPO and RTO are approved;
- recovery is exercised on the deployment platform;
- full recovery tests pass without real patient data.

## 11. Recommended implementation order

1. Shared manifest, checksum, redacted structured logging and safe-path helpers.
2. PostgreSQL custom-format backup/restore with empty-target protection.
3. DB-linked file manifest/archive/restore and extra/missing/corrupt detection.
4. Explicit post-restore session revocation plus bounded cleanup CLI options.
5. Synthetic full-stack recovery fixture and integrity manifest.
6. Current- and older-revision PostgreSQL recovery integration.
7. Health/readiness/security smoke and CI recovery layer.
8. Production runbooks, Compose storage boundary and final evidence report.
