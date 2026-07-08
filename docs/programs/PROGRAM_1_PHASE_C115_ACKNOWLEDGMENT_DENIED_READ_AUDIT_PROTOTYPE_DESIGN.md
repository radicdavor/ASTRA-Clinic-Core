# Program 1 Phase C115 - Acknowledgment Denied-Read Audit Prototype Design

Status: implementation design

## Purpose

C115 defines the implementation plan for selective denied-read audit on Human Review Acknowledgment read endpoints.

This is not a full read audit rollout.

## Events To Audit

Future C115-C125 runtime work may audit:

- authenticated user without `clinical_readiness.acknowledgments.read`
- API key denied by acknowledgment read endpoint
- non-human actor denied by acknowledgment read endpoint
- out-of-scope acknowledgment detail access
- invalid appointment access after actor context is known

## Events Not To Audit

Do not audit by default:

- successful acknowledgment list reads
- successful acknowledgment detail reads
- frontend refreshes
- repeated successful list/detail GETs
- normal missing acknowledgment ids that do not prove cross-scope access

## Permission Denied Boundary

Permission denied audit may record a minimal access/security event.

It must not change the response from denied to allowed.

## API Key Denied Boundary

API key attempts remain denied even when the key has a read scope.

Audit payload may include safe API key id and actor type.

## Out-of-Scope Detail Boundary

If a requested acknowledgment exists but belongs to another appointment, audit as scope denied.

Response semantics must remain not-found/denied according to existing route behavior.

## Invalid Appointment Boundary

Invalid appointment access may be audited as `appointment_not_found` after actor context is known.

Payload must not include clinical content.

## Audit Payload Minimum

Minimum payload:

- access type
- denial category
- appointment id if available
- acknowledgment id if attempted
- actor type
- actor user id if available
- actor api key id if available
- route/action
- result: `denied`

## Privacy Minimization

Payload must not include:

- full clinical reason text
- full acknowledgment reason text
- approval/clearance/override fields
- Outcome Evidence link
- Task link
- patient message link

## Rollback and Failure Expectations

If denied-read audit write fails, the access response must remain denied.

Audit failure must not grant access or mutate workflow state.

## Workflow Boundary

Denied-read audit must not:

- change appointment status
- create Task
- create Outcome Evidence
- send patient message
- imply approval, clearance or override

## Production Boundary

This prototype does not approve production or real patient data.

