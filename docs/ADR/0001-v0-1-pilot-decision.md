# ADR 0001: v0.1 Pilot Decision

## Status

Proposed

## Context

ASTRA Clinic Core has reached a v0.1-pilot candidate state for closed demo/pilot use with demo data only. The system includes appointment flow, inventory/material consumption, purchase receiving, invoice issue/payment, audit logging, public demo/real-data config, release notes, validation scripts and pilot feedback templates.

A maintainer command-level dry-run passed on 05-07-2026, but a human participant pilot dry-run has not yet been completed.

## Decision

Proceed to a closed human pilot dry-run using demo data only. Do not tag `v0.1-pilot` until the dry-run report and issue triage are reviewed and no P0/P1 issues remain open.

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

Complete the human v0.1 pilot dry-run, triage findings, fix any P0/P1 blockers, then decide whether to tag `v0.1-pilot`.
