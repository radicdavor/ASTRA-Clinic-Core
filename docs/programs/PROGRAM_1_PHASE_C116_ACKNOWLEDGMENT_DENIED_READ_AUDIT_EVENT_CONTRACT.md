# Program 1 Phase C116 - Acknowledgment Denied-Read Audit Event Contract

Status: event contract

## Canonical Event

`clinical_readiness_acknowledgment_read_denied`

This event records selected denied acknowledgment read attempts.

## Optional Future Split Events

Optional future split events:

- `clinical_readiness_acknowledgment_read_scope_denied`
- `clinical_readiness_acknowledgment_read_api_key_denied`

C115-C125 should prefer the canonical event unless split events become necessary.

## Allowed Payload Fields

Payload may include:

- actor id if available
- actor role if available
- actor type
- actor api key id if safe
- auth mechanism if safe
- appointment id if available
- patient id if safely known
- acknowledgment id if attempted
- route/action
- denial category
- request id if available
- timestamp through audit log metadata
- safe reason category
- result: `denied`

## Forbidden Payload Fields

Payload must not include:

- full clinical reason text
- full acknowledgment reason text
- approval_status
- clearance_status
- override_status
- outcome_evidence_id
- task_id
- appointment_status mutation
- patient_message_id
- patient-ready status
- clinical conclusion

## Denial Categories

Allowed denial categories:

- `missing_permission`
- `api_key_denied`
- `non_human_actor_denied`
- `appointment_not_found`
- `appointment_scope_mismatch`
- `acknowledgment_not_found_if_audited_later`
- `unexpected_error_if_audited_later`

## Boundary

The event is access/security evidence only.

It is not clinical evidence, Outcome Evidence, approval, clearance, override or workflow enforcement.

