# Program 1 Synthetic Read-Only UI Evaluation Track Phase E

## Executable External-Session Readiness Gate - Scope

Status: implemented.

## Purpose

Phase E converts the Phase C/D external-session prerequisites into a deterministic local command:

```bash
npm --prefix frontend run program1:evaluation-readiness
```

The gate confirms candidate identity, required artifacts, route and navigation presence, preflight/task counts, safety wording, prohibited primitive absence, and clean-worktree state.

## Gate Output

The command emits JSON containing:

- candidate name
- exact full commit SHA
- generation timestamp
- authorized scope
- total and passed check counts
- readiness decision
- failed checks
- prohibited authorizations

## Safety Decision

The only passing state is:

`READY FOR SEPARATELY AUTHORIZED EXTERNAL SESSION`

This means repository readiness only. It does not recruit a participant, obtain consent, authorize recording, execute a session, validate clinical usability, or authorize real data, production, clinical use, deployment, or go-live.

