# Next Action Before v0.1-pilot Tag

## Current Status

`v0.1-pilot` is no longer blocked by missing structured pilot answers. The maintainer provided structured answers: tasks 1-12 passed, real-data confusion was not observed, fiscalization confusion was not observed, and one P2 UX finding was recorded.

The P2 UX finding requested a visible hover/toast confirmation after actions such as patient entry and payment. This has been implemented as global toast feedback for successful create/update/delete actions.

V18 also implemented the patient identity/contextual help feedback: optional OIB, appointment patient search by name/contact/OIB, service context and help popovers for critical actions. Real OIB values remain forbidden in demo mode.

## Owner

- Maintainer / pilot facilitator

## Exact Next Human Action

1. Pull latest `main`.
2. Start the demo environment with Docker Compose.
3. Seed demo data.
4. Confirm `/api/public-config` returns `real_data_allowed=false`.
5. Open the frontend and confirm the demo banner is visible.
6. Run final validation checks.
7. Confirm GitHub CI is green after the latest V18 commit. Current status: green on `bdc282c`.
8. Review `docs/pilot_sessions/2026-07-05_human_pilot_01.md` and triage.
9. Confirm there are no open P0/P1 findings.
10. Tag `v0.1-pilot` only after explicit maintainer approval.

## Expected Evidence File

- `docs/pilot_sessions/2026-07-05_human_pilot_01.md`

Required evidence:

- participant role
- browser/device
- task completion table
- observed friction
- P0/P1/P2/P3 findings
- real-data confusion yes/no
- fiscalization confusion yes/no
- Go/No-Go recommendation

Structured answers received:

1. Login completed: Yes
2. Today's schedule found: Yes
3. Appointment detail opened: Yes
4. Appointment status changed: Yes
5. Material suggestion reviewed: Yes
6. Appointment completed with material consumption: Yes
7. Stock movement verified: Yes
8. Draft invoice created: Yes
9. Invoice issued: Yes
10. Payment recorded: Yes
11. Purchase order received: Yes
12. Audit trail found and understood: Yes
13. Real-data confusion observed: No
14. Fiscalization confusion observed: No
15. Observed friction or requested changes: visible hover/toast confirmation after actions.

## What Not To Build Yet

- broad clinical modules
- Google Calendar or OpenEMR integrations
- AI receptionist or new AI mutation flows
- real Croatian fiscalization
- alpha hardening not tied to pilot evidence
- production/real-data enablement

## Release Decision

- Accepted if final validation still passes and no P0/P1 remain open.
- Deferred while human pilot is pending or any P0/P1 exists.
- Waived only if maintainer explicitly accepts and documents the risk.
