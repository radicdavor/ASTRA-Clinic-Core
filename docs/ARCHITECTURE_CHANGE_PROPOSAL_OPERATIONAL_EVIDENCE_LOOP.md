# Architecture Change Proposal: Operational Evidence Loop

## Status

Proposed for maintainer review.

## Proposed Bible Addition

Add an operational evidence loop principle:

- Readiness is the pre-demo cockpit.
- Workspaces are where risks are inspected or resolved.
- `ActionButton` and `HelpHint` guide safe actions.
- Audit is the durable evidence of important changes.
- Pilot and release docs record the final human decision.

## Why This Is Needed

V19, V20 and V21 introduced strong building blocks: design language, workspaces, readiness and release governance. V22 connects those blocks into one operating model so users can move from risk to evidence without guessing.

## Current Implementation

- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- Readiness decision-impact metadata
- Readiness detail panel
- Patient Workspace summary strip
- More readable audit timeline

## Risk If Not Clarified

Without this principle, readiness may become a passive dashboard, workspaces may drift from release evidence, and audit may remain technically correct but operationally hard to understand.
