# Program 1 Phase C39 - Acknowledgment Request Response Contract

Status: passive schema contract

## Future Request Shape

Fields:

- `advisory_signal_key`
- `snapshot_id`
- `reason`
- `client_context_key`
- `idempotency_key`

Reason is required.

No client payload may claim approval, clearance, override, task creation, outcome evidence or patient messaging.

## Future Response Shape

Fields:

- `acknowledgment_key`
- `advisory_signal_key`
- `snapshot_id`
- `appointment_id`
- `patient_id`
- `actor_role`
- `reason`
- `created_at`
- `limitations`
- `warning`
- `is_decision: false`
- `is_clearance: false`
- `is_override: false`

## Runtime Boundary

The schema is passive.

It is not wired to a route or service.

