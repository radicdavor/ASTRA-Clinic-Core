# Program 1 Phase V1 - Prototype Access Boundary Model

This is a non-production access boundary model. It does not implement authentication, authorization, RBAC, least privilege, runtime access checks, permission seeds, endpoint guards, UI guards, production enforcement, or clinical workflow authorization.

## Actor types

The prototype recognizes these future actor labels for design purposes only:

| Actor type | Prototype purpose | Current status |
| --- | --- | --- |
| `clinical_owner` | Future clinical responsibility review. | design only |
| `clinician` | Future clinical user boundary. | design only |
| `clinical_reviewer` | Future review/support boundary. | design only |
| `operator` | Future operational support boundary. | design only |
| `administrator` | Future administrative boundary. | design only |
| `support_user` | Future support access boundary. | design only |
| `qa_validation_user` | Future validation evidence boundary. | design only |
| `security_privacy_reviewer` | Future security/privacy review boundary. | design only |
| `legal_compliance_reviewer` | Future legal/compliance review boundary. | design only |
| `data_governance_reviewer` | Future data governance review boundary. | design only |
| `read_only_auditor` | Future audit review boundary. | design only |
| `system_service_account` | Future service identity boundary. | design only |
| `external_integration_actor` | Future integration boundary. | design only |

No actor type is granted runtime permission by Phase V.

## Boundary statuses

| Status | Meaning |
| --- | --- |
| `allowed_for_demo_read_only` | May be modeled for demo/synthetic read-only contexts only. |
| `requires_future_governance` | Requires future owner review, implementation, validation, and approval before any use. |
| `prohibited` | Must remain blocked and non-authorized. |
| `not_applicable` | Not in scope for the current prototype. |

## Resource and action categories

| Resource/action category | Prototype boundary status | Explicit prohibition still active |
| --- | --- | --- |
| `clinical_readiness_snapshot` | `allowed_for_demo_read_only` | no write workflow, no production claim |
| `acknowledgment_advisory` | `allowed_for_demo_read_only` | advisory only, no clinical decision |
| `finding` | `allowed_for_demo_read_only` | no diagnosis confirmation |
| `open_question` | `allowed_for_demo_read_only` | no task or workflow enforcement |
| `extraction_record` | `allowed_for_demo_read_only` | no real AI/OCR or real-data extraction |
| `evidence_timeline` | `allowed_for_demo_read_only` | read-only/source-linked only |
| `review_workflow_metadata` | `requires_future_governance` | no approval/clearance/override |
| `demo_documentation` | `allowed_for_demo_read_only` | synthetic/demo-only |
| `configuration` | `requires_future_governance` | no production operation |
| `audit_event` | `requires_future_governance` | no production audit logging |
| `attachment_document` | `requires_future_governance` | no real or identifiable documents |
| `export` | `requires_future_governance` | no real-data export |
| `deletion` | `requires_future_governance` | no live deletion workflow |
| `patient_messaging` | `prohibited` | no patient messaging |
| `appointment_mutation` | `prohibited` | no appointment status mutation |
| `clinical_write_workflow` | `prohibited` | no clinical write workflow |
| `approval_clearance_override` | `prohibited` | no approval, clearance, or override capability |
| `task_engine` | `prohibited` | no Task engine |
| `outcome_evidence` | `prohibited` | no Outcome Evidence |
| `workflow_enforcement` | `prohibited` | no workflow enforcement |
| `real_patient_data` | `prohibited` | no real patient data |
| `phi_pii` | `prohibited` | no PHI/PII processing |
| `production_operation` | `prohibited` | no production operation |

Hard-coded prototype position: patient messaging, appointment mutation, clinical write workflow, approval/clearance/override, Task engine, Outcome Evidence, workflow enforcement, real patient data, PHI/PII, and production operation remain prohibited.
