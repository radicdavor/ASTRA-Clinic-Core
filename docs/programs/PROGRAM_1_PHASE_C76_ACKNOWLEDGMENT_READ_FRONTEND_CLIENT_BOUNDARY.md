# Program 1 Phase C76 - Acknowledgment Read Frontend Client Boundary

Status: frontend read-only client boundary

## Implemented Boundary

Frontend may define read-only types and GET client functions for acknowledgment list/detail.

Frontend must not define:

- POST acknowledgment client
- PATCH/PUT acknowledgment client
- DELETE acknowledgment client
- acknowledgment button
- approval/clearance/override action

## Safe Client Functions

Allowed:

- `getClinicalReadinessAcknowledgments`
- `getClinicalReadinessAcknowledgmentDetail`

Forbidden:

- `acknowledgeClinicalReadiness`
- `createClinicalReadinessAcknowledgment`
- `postClinicalReadinessAcknowledgment`

## UI Boundary

C76 does not add UI.

Any future UI must be read-only and must say acknowledgment is not approval, clearance, override or resolution.

