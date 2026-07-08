# Program 1 Phase C104 - Regression Notes

Status: documentation-only

## Implemented

- read audit policy design
- access audit vs clinical evidence boundary
- list/detail/denied/failed read distinctions
- audit-noise and privacy risk documentation
- policy preference for denied-read audit only as a future runtime candidate

## Runtime Changes

None.

## Not Implemented

- automatic read audit
- denied-read audit runtime implementation
- write endpoint
- acknowledgment action button
- approval
- clearance
- override
- Outcome Evidence
- Task engine
- appointment status mutation
- patient messaging

## Regression Position

Current read endpoints continue to be read-only and do not write read audit events by default.

