# ADR 0001: v0.1 Pilot Decision

## Status

Accepted

## Context

ASTRA Clinic Core has reached a v0.1-pilot candidate state for closed demo/pilot use with demo data only. The system includes appointment flow, inventory/material consumption, purchase receiving, invoice issue/payment, audit logging, public demo/real-data config, release notes, validation scripts and pilot feedback templates.

A maintainer command-level dry-run passed on 05-07-2026. The maintainer then completed the structured human pilot gate: tasks 1-12 passed, real-data confusion was not observed, fiscalization confusion was not observed, and one P2 UX finding was raised for clearer action confirmation.

## Decision

Proceed to a closed human pilot dry-run using demo data only. Do not tag `v0.1-pilot` until the dry-run report and issue triage are reviewed and no P0/P1 issues remain open.

V13 decision: defer `v0.1-pilot` tagging because the human participant pilot remains incomplete and has not been waived by the maintainer.

V14 decision: keep the release Deferred. No human pilot evidence or maintainer waiver was provided, so no feature work or tag should proceed.

V15 decision: keep the release Deferred. Human pilot evidence is still missing, no waiver exists, and no product feature work should proceed before the pilot gate.

Post-V15 update: maintainer/user completed an informal walkthrough and reported "Za sada dobro" with no issues reported. The release remains Deferred until structured pilot evidence fields are completed or explicitly waived.

V17 update: release remained Deferred because the structured pilot completion questions were still unanswered.

Post-V17 update: structured answers were provided. No P0/P1 blocker was reported. The P2 UX finding for action confirmation was fixed with global toast feedback for successful create/update/delete actions.

## Decision Options

1. Accepted - tag `v0.1-pilot` after the human pilot passes with no open P0/P1 issues.
2. Deferred - do not tag because P0/P1 was found or the human pilot remains incomplete.
3. Waived - maintainer explicitly permits tagging without a human pilot and documents the risk in this ADR and release notes.

Current status is Accepted for `v0.1-pilot` preparation because structured pilot evidence is complete and no P0/P1 blocker is open. Tagging still requires an explicit maintainer tag action after final checklist review.

## Consequences

- Feature expansion can proceed only after the pilot tag decision or an explicit maintainer direction.
- P0/P1 fixes take priority over new module or integration work.
- P2/P3 issues may be documented and deferred if release notes clearly describe them.
- Release tagging requires explicit checklist review.

## Real Data Status

Real patient data is not allowed. `REAL_DATA_ALLOWED` remains false by default, and `docs/REAL_DATA_READINESS_CHECKLIST.md` remains blocking.

## Fiscalization Status

Real Croatian fiscalization is not implemented. The current mode is noop/stub and must be presented as demo-only.

## Next Milestone

Run final validation checks, then tag `v0.1-pilot` only when the maintainer explicitly requests the tag.
