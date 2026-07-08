# Program 1 Phase C43 - Acknowledgment Idempotency Retry Policy

Status: idempotency design

## Purpose

This document defines a future idempotency policy for acknowledgment.

No runtime idempotency is implemented in C43.

## Future Request Field

`idempotency_key`

## Fingerprint Inputs

Future fingerprint should include:

- appointment id
- actor user id
- advisory signal key
- snapshot id if present
- cleaned reason

## Behavior

Same key and same fingerprint:

- return existing acknowledgment
- do not write duplicate audit event

Same key and different fingerprint:

- return conflict
- do not mutate workflow

## Client Payload Boundary

Client payload must not be trusted for clinical state.

The server must resolve appointment, patient, snapshot and actor context.

