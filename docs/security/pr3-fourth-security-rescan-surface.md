# PR #3 fourth security rescan affected surfaces

This inventory records the affected families before remediation. It is limited
to the three validated findings from the sealed scan of `acc6793`.

| Family | Current projection or constructor | Finding status | Required boundary |
| --- | --- | --- | --- |
| Appointment list/create/update/day, web intake, AI intake | `AppointmentOperationalOut` with `PatientOperationalIdentityOut` | Safe | Keep the existing narrow contract. |
| Reception appointment mutations | `AppointmentReceptionOut` with `PatientReceptionIdentityOut` | Safe | Keep contact data needed for identity verification; never add free-text notes. |
| Daily dashboard and reception day | Purpose-built scalar dashboard/reception schemas | Safe | Keep patient name and operational status only. |
| Patient journey list/detail/mutations | `JourneyOut.patient` uses local `PatientBrief` including `notes` | Affected | Reuse the canonical reception identity projection without `notes`. |
| Global `/api/search` patient group | Raw `Patient` ORM rows | Affected | Typed global identity DTO and an explicit column projection. |
| Global `/api/search` appointment group | Raw `Appointment` ORM rows | Affected sibling | Typed operational search DTO and an explicit column projection without notes. |
| Global `/api/search` service group | Raw `Service` ORM rows | Affected sibling | Typed operational service DTO and an explicit column projection. |
| Workflow task and activity projections | IDs, labels and purpose-specific operational fields | Safe | No broad nested patient serializer. |
| Manual clinical-document create | Omits `record_classification` and inherits `clinical` | Affected | Persist `unclassified` explicitly. |
| Browser upload and canonical ingestion | Explicit `unclassified` | Safe | Preserve fail-closed behavior. |
| Signed report generation | Explicit `clinical` after human signature | Trusted exception | Preserve the explicit trusted classification. |
| Synthetic reviewed-document seed | Inherits the model default | Affected sibling | Mark the intentionally reviewed synthetic records explicitly. |
| ORM and database default | `clinical` | Affected sibling | Change future-row defaults to `unclassified`; do not rewrite history. |

The remediation must not create role-dependent JSON shapes. Operational
endpoints always return narrow DTOs; authorized clinical detail remains on its
existing explicit endpoints.
