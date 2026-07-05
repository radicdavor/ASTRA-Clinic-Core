# v11 Backlog From Pilot

Derived from the 05-07-2026 maintainer dry-run. This backlog is provisional and must be updated after the first human closed pilot.

Human pilot findings override maintainer speculation. No alpha hardening work starts until P0/P1 findings from the human pilot are reviewed and resolved or explicitly waived.

## P0/P1 Blockers

- None found during command-level maintainer dry-run.
- Human browser pilot still required before final tag decision.

## P2 Usability Fixes

- Capture real participant feedback for dashboard, appointment detail, material consumption, invoice/payment and purchase receiving screens.
- Decide whether static frontend smoke is enough for v0.1-pilot or whether a minimal Playwright smoke is required.

## P3 Polish

- Review Croatian wording after human pilot.
- Review table density and button labels after live observation.

## Alpha Hardening Candidates

- Minimal browser e2e flow: login, dashboard, appointment detail.
- More readable audit before/after diff.
- Clearer release health dashboard or admin status page.

## Integrations Deferred

- Google Calendar integration.
- OpenEMR integration.
- Accounting integrations.

## Clinical Modules Deferred

- Gastroenterology module v1.
- Endoscopy-specific workflow.
- Dermatology/aesthetics module expansion.

## Real-Data Blockers

- GDPR/DPIA review.
- Production hosting and monitoring.
- Backup restore test.
- Real fiscalization provider.
- Stronger user lifecycle and access review process.
- Read access audit strategy.
