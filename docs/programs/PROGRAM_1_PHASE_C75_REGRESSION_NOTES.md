# Program 1 Phase C75 - Regression Notes

Status: read-only endpoint prototype

## Implemented

- added internal read service helpers for appointment-scoped acknowledgment list/detail
- added read-only list endpoint
- added read-only detail endpoint
- added read-only permission `clinical_readiness.acknowledgments.read`
- seeded read permission for admin and physician demo/pilot roles
- denied API key read by endpoint even if read scope exists
- added backend regression coverage

## Not Implemented

- POST/PATCH/PUT/DELETE acknowledgment endpoint
- frontend write client
- UI action button
- write permission seed
- approval
- readiness clearance
- override
- Task engine
- Outcome Evidence
- appointment status mutation
- patient messaging

## Safety Notes

Read endpoints do not write audit by default.

Read endpoints do not mutate appointment or workflow state.

