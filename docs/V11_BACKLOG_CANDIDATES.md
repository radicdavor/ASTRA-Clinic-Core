# v11 Backlog Candidates

This file captures future work without expanding scope before the v0.1-pilot dry-run.

## P0/P1 Pilot Blockers

- Fix any data corruption, permission bypass, missing demo banner, stock mismatch, invoice/payment state issue, or blocked core demo workflow found during pilot.

## Frontend Workflow Refinement

- Reduce extra clicks in appointment, material consumption, purchase receiving and invoice workflows.
- Improve Croatian labels and error messages from pilot feedback.
- Add Playwright smoke for login, dashboard and appointment detail.

## Audit/Security

- Improve audit filtering and before/after diff readability.
- Add stronger access logging for read operations before real-data use.
- Review API key lifecycle, expiration and scope defaults.

## Module System

- Add versioned module migrations/data packs.
- Improve module enable/disable UX.
- Add module-level test fixtures.

## Gastroenterology Module v1

- Expand gastro service catalog after core pilot blockers are resolved.
- Add gastro-specific material templates and reporting needs from real workflow interviews.

## Google Calendar Integration

- Define one-way or two-way sync requirements.
- Add conflict and source-of-truth policy before implementation.

## OpenEMR Integration

- Define patient/appointment mapping.
- Decide integration boundaries so ASTRA remains scheduling/patient-flow focused.

## AI Receptionist Integration

- Keep mutation actions scoped through existing API key permissions.
- Add dry-run mode and operator approval before real scheduling changes.

## Croatian Fiscalization

- Replace noop/stub provider with real provider only after legal/accounting requirements are confirmed.
- Add retry, failure handling and audit of every fiscalization attempt.
