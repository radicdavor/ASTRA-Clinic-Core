# Program 1 Phase C40 - Acknowledgment Error States Contract

Status: error contract only

## Purpose

This document defines future error states for a potential acknowledgment endpoint.

No endpoint is implemented in C40.

## Future Error States

- `400`: malformed request
- `401`: authentication required
- `403`: user lacks acknowledgment permission
- `404`: appointment, snapshot or advisory context not found
- `409`: duplicate idempotency key with conflicting payload
- `422`: reason missing or invalid signal context

## Required Error Wording

Errors must not imply:

- approval failed
- clearance failed
- override failed
- workflow was blocked
- patient is unsafe

## Non-Blocking Behavior

Failure to acknowledge must not change appointment status.

It must not create Task, Outcome Evidence or patient message.

