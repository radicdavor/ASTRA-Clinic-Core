# Program 1 Phase C72 - Acknowledgment Read Response Schema Contract

Status: response schema contract

## Svrha

C72 definira read-only response shape za Human Review Acknowledgment.

Response smije prikazati samo da je signal pregledan, ne da je problem rijesen.

## List Item Fields

List item mora ukljuciti:

- `id`
- `acknowledgment_key`
- `appointment_id`
- `patient_id`
- `advisory_signal_key`
- `snapshot_id`
- `actor_user_id`
- `actor_role`
- `reason`
- `limitations`
- `schema_version`
- `created_at`
- `safe_disclaimer`
- `is_decision=false`
- `is_clearance=false`
- `is_override=false`

## Detail Fields

Detail response mora ukljuciti:

- all list fields
- `warning`

Warning mora reci da acknowledgment nije clinical approval, readiness clearance, override, Outcome Evidence ili dozvola za postupak.

## List Response

List response mora ukljuciti:

- `appointment_id`
- `acknowledgments`
- `count`
- `is_read_only=true`
- `warning`

## Forbidden Fields

Response ne smije ukljuciti:

- `approval_status`
- `clearance_status`
- `override_status`
- `outcome_evidence_id`
- `task_id`
- `appointment_status`
- `patient_message_id`
- `procedure_approved`
- `patient_ready`
- `resolved_at`

## Zakljucak

Read schema moze biti implementirana prije endpointa samo ako ostaje passive response shape.

