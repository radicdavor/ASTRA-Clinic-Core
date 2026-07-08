# Program 1 Phase C105 - Acknowledgment Read Audit Event Taxonomy

Status: future event taxonomy

## Purpose

C105 defines possible future read audit events for acknowledgment access.

No runtime audit events are implemented in this phase.

## Event: `clinical_readiness_acknowledgment_list_read`

Trigger condition:

- user successfully reads appointment-scoped acknowledgment list

Actor metadata:

- actor user id
- actor role if available
- actor type

Payload context:

- appointment id
- patient id if safely resolved
- request id
- result: `success`

Privacy caveat:

- do not include full acknowledgment reason text

Retention expectation:

- access-audit retention class, not clinical evidence retention

Outcome boundary:

- not Outcome Evidence and not clinical approval

## Event: `clinical_readiness_acknowledgment_detail_read`

Trigger condition:

- user successfully reads one acknowledgment detail record

Actor metadata:

- actor user id
- actor role if available
- actor type

Payload context:

- appointment id
- patient id
- acknowledgment id
- request id
- result: `success`

Privacy caveat:

- do not include full clinical reason text unless explicitly approved later

Retention expectation:

- access-audit retention class

Outcome boundary:

- not Outcome Evidence and not a clinical decision

## Event: `clinical_readiness_acknowledgment_read_denied`

Trigger condition:

- read request is denied because actor is unauthenticated, lacks permission, is an API key, is an AI/system actor or is out of appointment scope

Actor metadata:

- actor user id if known
- actor api key id if safe
- actor type

Payload context:

- appointment id if safely parsed
- acknowledgment id if requested
- request id
- result: `denied`
- safe denial category

Privacy caveat:

- avoid leaking existence of acknowledgment records across appointments

Retention expectation:

- security/access-review retention class

Outcome boundary:

- not Outcome Evidence and not clinical workflow state

## Event: `clinical_readiness_acknowledgment_read_failed`

Trigger condition:

- read request fails due to missing record, invalid route context or unexpected server-side failure

Actor metadata:

- actor metadata if available

Payload context:

- appointment id if safely parsed
- acknowledgment id if requested
- request id
- result: `failed`
- safe error category

Privacy caveat:

- avoid detailed clinical payload or reason text

Retention expectation:

- access/security retention class

Outcome boundary:

- not Outcome Evidence and not clinical failure state

## Implementation Position

The preferred first runtime event remains:

`clinical_readiness_acknowledgment_read_denied`

List/detail success read events remain deferred because of audit-noise risk.

