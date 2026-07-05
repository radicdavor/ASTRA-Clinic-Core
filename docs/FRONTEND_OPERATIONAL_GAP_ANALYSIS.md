# Frontend Operational Gap Analysis

Quality Gate Sprint review of the current React UI.

## Current Coverage

- Daily schedule is available and supports quick status updates.
- Patients, appointments, services, modules and audit log have basic screens.
- Inventory, suppliers, purchase orders and invoices have list-oriented screens.

## Gaps

- Purchase order receiving by line is not yet available in the UI.
- Ordered, received and remaining purchase quantities are not presented as an operational receive workflow.
- Stock transfer with mandatory reason is not yet available in the UI.
- Write-off with mandatory reason is not yet available in the UI.
- Complete appointment with material consumption is not yet available as a guided workflow.
- Draft invoice from appointment is not yet exposed from the appointment screen.
- Invoice issue and payment recording are not yet available as primary UI actions.
- Audit filters exist at API level but the UI is still basic.
- API key management is not yet exposed in the UI.

## Top 3 Recommended Workflows

1. Complete appointment with material consumption.
2. Purchase order receiving.
3. Invoice issue and payment recording.

These should be implemented after PostgreSQL-backed API quality gates remain green. No cosmetic redesign is recommended before these workflows are operational.
