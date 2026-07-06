# Architecture Change Proposal: Object-Centered Workspaces

## Status

Proposed for maintainer review.

## Proposed Bible Addition

Add an explicit workspace principle:

- ASTRA object screens should be organized as workspaces.
- A workspace centers one object and gathers identity, status, related records, actions, warnings and audit.
- Patient Workspace is the primary patient object screen.
- Appointment Workspace is the operational workflow screen for visit flow, materials, invoice connection and audit.
- Cross-object navigation should preserve context, especially Patient -> Appointment -> Invoice -> Audit.

## Why This Is Needed

As ASTRA grows, separate tables and forms can make the system feel fragmented. The Architecture Bible says ASTRA should become an operating system for the clinic. Object-centered workspaces make that principle concrete without adding unnecessary medical scope.

## Current Implementation

- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `frontend/src/components/workspace/`
- Patient Workspace at `/patients/:id`
- Appointment detail aligned with workspace layout
- Patient appointment and invoice endpoints

## Risk If Not Clarified

Future modules may create unrelated pages with inconsistent navigation. That would weaken the shared language of the system and increase cognitive load for clinic users.
