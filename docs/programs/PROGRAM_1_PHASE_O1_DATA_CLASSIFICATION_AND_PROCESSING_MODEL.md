# Program 1 Phase O1 - Data Classification and Processing Model

All real patient data categories remain not approved, not implemented, not validated, and not allowed.

| Data Category | Example Description | Synthetic/Demo Allowed Now? | Real-Data Allowed Now? | Required Future Controls | Required Owner Type | Required Evidence Before Real-Data Consideration | Risk If Mishandled | Current Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| synthetic demo data | clearly fake demo content | yes | no | synthetic labeling and review | Data governance owner | synthetic data policy | demo confusion | demo-only allowed |
| test data | non-real test fixtures | yes | no | test-data isolation | Engineering owner | fixture review | accidental real data | demo/test only |
| configuration data | app configuration | yes | no | secrets/config separation | Engineering/security owner | config inventory | environment leakage | not real-data use |
| operator account data | demo user accounts | yes | no | account policy | Operations/security owner | account inventory | access confusion | demo-only |
| clinical-like demo data | fake clinical scenarios | yes | no | demo-only labeling | Clinical/product owner | scenario review | mistaken clinical truth | demo-only |
| real patient identifiers | names, IDs, contact details | no | no | PHI/PII classification and RBAC | Data governance owner | classification policy | privacy breach | not approved |
| direct PHI/PII | direct patient-identifying data | no | no | legal basis, access logging | Legal/privacy owner | legal/compliance review | unlawful processing | not allowed |
| indirect identifiers | quasi-identifiers | no | no | minimization and re-identification review | Privacy owner | privacy risk assessment | re-identification | not allowed |
| clinical notes | clinician-authored notes | no | no | clinical data governance | Clinical/data owner | clinical record policy | unsafe disclosure | not allowed |
| diagnoses | diagnosis records | no | no | clinical responsibility model | Clinical owner | sign-off and validation package | clinical harm | not allowed |
| medications | medication records | no | no | medication safety governance | Clinical owner | medication data policy | patient safety risk | not allowed |
| procedures | procedure records | no | no | source-linking and responsibility controls | Clinical owner | procedure data policy | misinterpretation | not allowed |
| endoscopy findings | endoscopy clinical findings | no | no | specialty review and provenance | Clinical owner | specialty governance | clinical misuse | not allowed |
| histopathology findings | pathology reports/findings | no | no | document provenance and retention | Clinical/data owner | source integrity review | high sensitivity | not allowed |
| laboratory results | lab values/reports | no | no | source validation and units policy | Clinical/data owner | lab data policy | inaccurate use | not allowed |
| imaging references | imaging metadata/links | no | no | attachment/storage controls | Clinical/security owner | storage assessment | disclosure risk | not allowed |
| appointments | scheduling records | no | no | appointment mutation controls | Operations/product owner | workflow policy | status mutation risk | not allowed |
| communications | patient/staff messages | no | no | messaging governance | Legal/product owner | communication policy | unauthorized contact | not allowed |
| attachments/documents | uploaded documents | no | no | document storage security | Security/data owner | storage and access review | PHI exposure | not allowed |
| audit logs | access/action logs | no | no | audit retention and minimization | Security/compliance owner | audit policy | privacy/security gaps | not real-data approved |
| system logs | application/system logs | yes if non-sensitive | no | redaction and log retention | Security/operations owner | logging review | PHI leakage | no PHI logging |
| backup data | backups and dumps | no | no | encryption and restore controls | Operations/security owner | restore drill evidence | broad data loss | not allowed |
| exported data | downloads/exports | no | no | export approval and audit | Data/legal owner | export procedure | uncontrolled disclosure | not allowed |
| deleted/archived data | retained deleted records | no | no | deletion and archival policy | Legal/data owner | lifecycle policy | retention breach | not allowed |
