# PR #3 Sixth Security Rescan — Affected Surface

## Scope

This inventory covers only the three sealed Medium/P2 findings on PR #3 head
`f50cc71`: legacy classification trust, client-asserted access audit events,
and Patient–Clinic provenance for clinical documents.

## Legacy classification chain

| Migration | Change | Trust assumption | Result |
|---|---|---|---|
| `0060` | Adds `is_clinical_record` with `true` default | Legacy documents are clinical records | Unsafe as an authorization signal |
| `0061` | Adds `record_classification` with `clinical` default | Existing records are trusted clinical content | Unsafe without review provenance |
| `0063` | Adds institution provenance | Institution scope can be resolved | Necessary, but not proof of review |
| `0068` | Changes future default to `unclassified` | New records fail closed | Safe for new rows only |
| `0069` | Adds explicit classification-review provenance and demotes unsupported legacy trust | Review, medical reviewer, clinic/institution consistency and active Patient–Clinic provenance are required | Safe forward correction |

`is_clinical_record` remains intake/legacy intent metadata. It is not sufficient
to grant institution-wide clinical visibility.

## Sensitive-access producers

| Claimed action | Prior producer | Canonical server workflow | Decision |
|---|---|---|---|
| `patient.viewed` | client direct endpoint | authorized patient/clinical-history route | direct assertion disabled |
| `clinical_workspace.opened` | client direct endpoint | journey/workspace bootstrap and clinical-form routes | direct assertion disabled |
| `clinical_form.viewed` | client direct endpoint | clinical-form route | direct assertion disabled |
| `signed_report.viewed` | client direct endpoint | signed-report detail route | direct assertion disabled |
| `source_document.viewed` | client direct endpoint | document source/detail route | direct assertion disabled |
| `source_document.downloaded` | client direct endpoint | source download route | direct assertion disabled |
| `billing_details.viewed` | client direct endpoint | authorized billing detail route | direct assertion disabled |
| `clinical_report.printed` | client direct endpoint | server report-print command | direct assertion disabled |
| `audit_log.viewed` | server list route | audit list route | internal server event retained |
| `patient_export.created` | server export workflow | export command | already direct-disabled |

The compatibility endpoint remains present but returns a controlled conflict
for all authoritative actions and does not write an `AuditLog` row.
Client-generated `interaction_id` values are not used as forensic proof.
Patient detail, journey detail, clinical-form detail and invoice detail record
their access on the server after successful scope resolution. Document,
signed-report and print routes retain their existing server-owned events.
Separate successful HTTP reads remain separate forensic events.

## Clinical-document write and classification paths

| Path | Resolved clinic | Patient–Clinic validation | Initial/trusted classification |
|---|---|---|---|
| manual create | payload, appointment or actor membership | active association required | `unclassified` |
| patient-scoped create | same as manual create | active association required | `unclassified` |
| placeholder upload | payload, appointment or actor membership | active association required | `unclassified` |
| journey ingestion | journey clinic | active association and matching appointment required | `unclassified` |
| generated signed report | activity/journey clinic | active association and matching appointment required | `clinical`, with signer-backed classification review |
| classification review | existing document clinic | revalidated before transition | medical reviewer and timestamp recorded |
| OCR/classification job | existing document | does not create trusted classification | candidate only |
| demo seed | synthetic gastro clinic | explicit synthetic association | explicit synthetic medical reviewer |

No path auto-creates a Patient–Clinic association as a side effect of document
creation or classification.
