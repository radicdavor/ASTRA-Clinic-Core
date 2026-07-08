# Program 1 Phase V3 - Real-Data Boundary Prototype

Purpose: model how future controls could identify or block PHI/PII/real patient data risk in non-production contexts.

Phase V does not ingest real patient data, does not process PHI/PII, does not add upload/import endpoints, does not persist documents, does not inspect real clinical text, and does not approve any real-data workflow.

Allowed placeholder examples must remain visibly synthetic, such as:

- `SYNTHETIC_PATIENT_ID`
- `DEMO_ONLY_NAME`
- `EXAMPLE_DATE`

No realistic patient names, dates of birth, phone numbers, MRNs, OIBs, addresses, documents, or clinical narratives are introduced by Phase V.

## Boundary categories

| Boundary category | Current decision | Required future controls | Explicit prohibition still active |
| --- | --- | --- | --- |
| `synthetic_demo_data` | allowed only in demo/synthetic context | labeling, separation, validation | no production or real-data claim |
| `clinical_like_demo_data` | allowed only if clearly synthetic and labeled | labeling, review, synthetic-data guard | no real clinical narrative |
| `operator_metadata` | requires future governance | data minimization, access boundary, audit | no production access claim |
| `configuration_metadata` | requires future governance | owner review, audit, environment separation | no production operation |
| `real_patient_identifier` | prohibited | legal/privacy/security approval, validation | no real patient identifiers |
| `direct_phi_pii` | prohibited | legal/privacy/security approval, validation | no direct PHI/PII |
| `indirect_identifier` | prohibited | legal/privacy/security approval, validation | no indirect identifiers |
| `clinical_note` | prohibited if real or identifiable | real-data governance, redaction, audit, validation | no real/identifiable note |
| `document_attachment` | prohibited if real or identifiable | storage controls, scanning, retention, legal review | no real/identifiable attachment |
| `external_import` | prohibited unless future governance approves | ingestion governance, validation, incident controls | no external import |
| `free_text_input` | prohibited for PHI/PII unless future governance approves | input controls, warnings, review, validation | no PHI/PII free text |

## Current decision

Real patient data remains not approved, not implemented, not validated, and not allowed. PHI/PII processing remains not approved, not implemented, not validated, and not allowed.
