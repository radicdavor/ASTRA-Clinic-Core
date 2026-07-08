# Program 1 Phase C41 - Acknowledgment Permission Boundary

Status: permission boundary contract

## Purpose

This document defines the future permission boundary for acknowledgment.

No permission is implemented in C41.

## Future Permission

Possible future permission:

`clinical_readiness.acknowledgments.write`

This permission is not seeded now.

## Allowed Actors

Future write access may be limited to:

- physician
- explicitly authorized admin

## Denied By Default

- API keys
- AI agents
- receptionist
- unauthenticated users

## Boundary

Permission would allow only recording review context.

It would not allow:

- approval
- clearance
- override
- appointment status mutation
- Task creation
- Outcome Evidence
- patient messaging

