# Next Action Before v0.1-pilot Tag

## Current Block

`v0.1-pilot` is blocked because the human participant browser pilot has not been completed and no maintainer waiver has been documented.

## Owner

- Maintainer / pilot facilitator

## Exact Next Human Action

1. Pull latest `main`.
2. Start the demo environment with Docker Compose.
3. Seed demo data.
4. Confirm `/api/public-config` returns `real_data_allowed=false`.
5. Open the frontend and confirm the demo banner is visible.
6. Run the human pilot using `docs/pilot_sessions/HUMAN_PILOT_FACILITATOR_SHEET.md`.
7. Record the session in `docs/pilot_sessions/2026-07-05_human_pilot_01.md`.
8. Update `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`.
9. Create GitHub issues for findings or document `to-create` payloads.
10. Update `docs/V0_1_GO_NO_GO_MATRIX.md`.
11. Update ADR 0001 to Accepted, Deferred or Waived.

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

## What Not To Build Yet

- broad clinical modules
- Google Calendar or OpenEMR integrations
- AI receptionist or new AI mutation flows
- real Croatian fiscalization
- alpha hardening not tied to pilot evidence
- production/real-data enablement

## Release Decision

- Accepted only if human pilot completes and no P0/P1 remain open.
- Deferred while human pilot is pending or any P0/P1 exists.
- Waived only if maintainer explicitly accepts and documents the risk.
