# Program 1 Phase C30 - Acknowledgment Permission Governance

Status: permission design only

## Purpose

This document defines future permission governance for Human Review Acknowledgment.

C30 does not add permissions to seed data.

## Future Permission Names

Potential future permissions:

- `clinical_readiness.acknowledgments.read`
- `clinical_readiness.acknowledgments.write`

These names are reserved for design discussion only.

## Default Role Position

Future role policy should start restrictive:

- admin: review only after governance decision
- physician: possible writer after governance decision
- nurse: no write by default
- receptionist: no write
- API key: denied by default
- AI agent: denied by default

## Write Governance

Write access must require:

- human actor
- explicit reason
- audit event
- appointment context
- advisory signal context

## Forbidden Permission Effects

Permission must not allow:

- approval
- clearance
- override
- appointment status mutation
- Task creation
- Outcome Evidence
- patient messaging

## Runtime Status

No permission is implemented in C30.

