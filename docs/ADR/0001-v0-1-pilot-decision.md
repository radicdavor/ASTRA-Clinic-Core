# ADR 0001: v0.1 Pilot Decision

## Status

Deferred

## Context

ASTRA Clinic Core has reached a v0.1-pilot candidate state for closed demo/pilot use with demo data only. The system includes appointment flow, inventory/material consumption, purchase receiving, invoice issue/payment, audit logging, public demo/real-data config, release notes, validation scripts and pilot feedback templates.

A maintainer command-level dry-run passed on 05-07-2026, but a human participant pilot dry-run has not yet been completed.

## Decision

Proceed to a closed human pilot dry-run using demo data only. Do not tag `v0.1-pilot` until the dry-run report and issue triage are reviewed and no P0/P1 issues remain open.

V13 decision: defer `v0.1-pilot` tagging because the human participant pilot remains incomplete and has not been waived by the maintainer.

V14 decision: keep the release Deferred. No human pilot evidence or maintainer waiver was provided, so no feature work or tag should proceed.

## Decision Options

1. Accepted - tag `v0.1-pilot` after the human pilot passes with no open P0/P1 issues.
2. Deferred - do not tag because P0/P1 was found or the human pilot remains incomplete.
3. Waived - maintainer explicitly permits tagging without a human pilot and documents the risk in this ADR and release notes.

Current status is Deferred because human pilot results do not exist yet and no maintainer waiver has been recorded.

## Consequences

- Feature expansion remains deferred.
- P0/P1 fixes take priority over new module or integration work.
- P2/P3 issues may be documented and deferred if release notes clearly describe them.
- Release tagging requires explicit checklist review.

## Real Data Status

Real patient data is not allowed. `REAL_DATA_ALLOWED` remains false by default, and `docs/REAL_DATA_READINESS_CHECKLIST.md` remains blocking.

## Fiscalization Status

Real Croatian fiscalization is not implemented. The current mode is noop/stub and must be presented as demo-only.

## Next Milestone

Complete the human v0.1 pilot dry-run, triage findings, fix any P0/P1 blockers, then decide whether to tag `v0.1-pilot` or explicitly waive the human pilot gate.
