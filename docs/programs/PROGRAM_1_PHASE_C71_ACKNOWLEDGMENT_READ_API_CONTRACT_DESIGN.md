# Program 1 Phase C71 - Acknowledgment Read API Contract Design

Status: read-only API contract

## Svrha

C71 definira appointment-scoped read-only API contract za Human Review Acknowledgment zapise.

Read API ne znaci workflow approval, readiness clearance, override, resolution ili production readiness.

## Proposed Routes

List:

`GET /api/appointments/{appointment_id}/clinical-readiness/acknowledgments`

Detail:

`GET /api/appointments/{appointment_id}/clinical-readiness/acknowledgments/{acknowledgment_id}`

## Appointment-Scoped Boundary

Svaki read mora biti scoped na appointment.

Detail ruta mora odbiti acknowledgment koji postoji, ali ne pripada trazenom appointmentu.

## Auth and Permission

Read endpoint mora zahtijevati:

- authenticated actor
- read-only permission `clinical_readiness.acknowledgments.read`

Read permission ne smije dati write capability.

## Response Fields

List item:

- acknowledgment id/key
- appointment id
- patient id
- advisory signal key
- optional snapshot id
- actor user id
- actor role
- reason
- limitations
- schema version
- created_at
- safe disclaimer

Detail response:

- all list fields
- full reason
- advisory signal relation
- snapshot relation if present
- warning that acknowledgment is not approval, clearance, override, Outcome Evidence or procedure permission

## Sorting and Filtering

Default sorting:

- newest first by `created_at desc`
- deterministic tie-breaker by `id desc`

Initial filter:

- appointment scope only

Future filters may include advisory signal key or snapshot id, but must remain read-only.

## Empty State

If no acknowledgments exist:

- return `count=0`
- return empty list
- do not treat absence as clinical risk resolution

## Error States

- `401` unauthenticated
- `403` missing read permission
- `404` appointment not found
- `404` acknowledgment not found for appointment

## No Write Behavior

Read API must not:

- create acknowledgment
- update acknowledgment
- delete acknowledgment
- write audit by default
- change appointment status
- create Task
- create Outcome Evidence
- send patient message
- approve, clear or override readiness

