# Program 1 Phase V2 - Prototype Audit Event Model

This is a passive audit event design. Phase V does not implement audit logging, persistence, immutability, retention, review screens, alerts, dashboards, production auditability, or validation.

## Future audit event categories

| Event category | Why it matters | Current status |
| --- | --- | --- |
| `record_view` | Future traceability for record reads. | design only |
| `record_search` | Future traceability for search access. | design only |
| `timeline_access` | Future traceability for timeline reads. | design only |
| `finding_access` | Future traceability for finding reads. | design only |
| `open_question_access` | Future traceability for open question reads. | design only |
| `extraction_record_access` | Future traceability for extraction record reads. | design only |
| `configuration_view` | Future traceability for configuration visibility. | design only |
| `export_attempt` | Future boundary signal for export attempts. | design only |
| `deletion_attempt` | Future boundary signal for deletion attempts. | design only |
| `admin_action_attempt` | Future privileged action traceability. | design only |
| `integration_access_attempt` | Future integration boundary traceability. | design only |
| `security_event` | Future security review input. | design only |
| `privacy_sensitive_access_attempt` | Future privacy-sensitive boundary signal. | design only |
| `real_data_boundary_attempt` | Future real-data no-go boundary signal. | design only |
| `phi_pii_boundary_attempt` | Future PHI/PII no-go boundary signal. | design only |
| `patient_messaging_attempt` | Future prohibited messaging boundary signal. | design only |
| `appointment_mutation_attempt` | Future prohibited appointment mutation boundary signal. | design only |
| `clinical_write_attempt` | Future prohibited clinical write boundary signal. | design only |
| `approval_clearance_override_attempt` | Future prohibited approval/clearance/override boundary signal. | design only |
| `task_engine_attempt` | Future prohibited Task engine boundary signal. | design only |
| `outcome_evidence_attempt` | Future prohibited Outcome Evidence boundary signal. | design only |
| `workflow_enforcement_attempt` | Future prohibited workflow enforcement boundary signal. | design only |
| `production_boundary_attempt` | Future production no-go boundary signal. | design only |

## Minimum future fields

Future audit design would require, where relevant:

- `timestamp`
- `actor_id`
- `actor_type`
- `role_context`
- `action`
- `resource_type`
- `resource_id`
- `result`
- `reason`
- `environment`
- `correlation_id`
- `source`
- `boundary_status`

These fields are not implemented or persisted by Phase V. They are a planning model only.

## Non-approval

The model is not production audit logging, not audit retention, not audit immutability, not audit review approval, and not validation evidence for production or real-data use.
