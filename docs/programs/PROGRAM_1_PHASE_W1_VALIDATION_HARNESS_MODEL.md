# Program 1 Phase W1 - Validation Harness Model

This document defines the future non-production validation harness model for Program 1 boundary prototypes.

## Harness areas

| Harness area | Purpose | Future evidence | Current status |
| --- | --- | --- | --- |
| access boundary harness | Prove prohibited access categories remain prohibited. | test output, reviewed assertions | planned only |
| audit event harness | Prove boundary-attempt event categories are represented. | model coverage evidence | planned only |
| real-data boundary harness | Prove real-data/PHI/PII categories remain prohibited. | negative test evidence | planned only |
| non-approval language harness | Prove docs/prototype wording does not imply approval. | wording scan evidence | planned only |
| clinical workflow no-go harness | Prove patient messaging, appointment mutation and write workflows remain prohibited. | negative test evidence | planned only |
| production/go-live no-go harness | Prove production and go-live boundaries are not lifted. | negative test evidence | planned only |

## Harness rules

- Use synthetic/demo-only inputs.
- Do not introduce real patient data examples.
- Do not use PHI/PII.
- Do not require production auth/authz/RBAC.
- Do not require database migrations or live services.
- Do not create workflow enforcement.
- Do not interpret test passage as production approval.

Phase W documents the harness model only.
