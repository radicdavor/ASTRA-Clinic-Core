# Program 1 Phase C34 - Permission Seed No-Go Hardening

Status: permission no-go guard

## Purpose

C34 documents why acknowledgment permissions are intentionally not seeded.

## Current Decision

Do not seed:

- `clinical_readiness.acknowledgments.read`
- `clinical_readiness.acknowledgments.write`
- `clinical_readiness.acknowledgments.manage`

## Reason

Permissions without runtime design can create a false sense that the feature is approved.

Acknowledgment persistence, endpoint and UI action remain no-go.

## Future Condition

Permissions may be added only after:

- persistence design is approved
- migration is approved
- endpoint contract is approved
- audit event is approved
- UI copy is reviewed
- real-data and production guardrails remain explicit

