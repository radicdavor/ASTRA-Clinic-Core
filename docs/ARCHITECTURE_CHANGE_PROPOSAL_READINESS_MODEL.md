# Architecture Change Proposal: Readiness Model

## Status

Proposed for maintainer review.

## Proposed Bible Addition

Add readiness as a read-only operational risk layer:

- Readiness Cockpit is the pre-demo and pre-pilot entry point.
- Readiness checks should link to workspaces or operational screens when possible.
- Readiness is not production, GDPR, fiscalization or real-data approval.
- Critical readiness status blocks demo unless explicitly waived by the maintainer.
- Warnings may be acceptable for demo only when understood and documented.

## Why This Is Needed

V20 introduced both workspaces and a readiness cockpit. V21 connects them so readiness does not become a separate checklist disconnected from actual clinic operations.

## Current Implementation

- `docs/ASTRA_READINESS_MODEL.md`
- `/api/readiness`
- `/readiness`
- target paths on readiness checks
- human pilot evidence readiness reminder

## Risk If Not Clarified

Without this principle, readiness could be misunderstood as compliance approval or become a passive dashboard with no operational navigation.
