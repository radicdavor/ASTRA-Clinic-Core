# Program 1 Phase C25 - Acknowledgment Advisory CI Gate

Status: CI and regression gate

## Purpose

The C25 gate protects advisory signal and human review acknowledgment safety before any future runtime work.

## Backend Gate

Required backend checks:

- targeted snapshot regression tests
- targeted advisory signal schema tests
- targeted review acknowledgment schema tests
- full backend test suite
- database migrations

## Frontend Gate

Required frontend checks:

- TypeScript typecheck
- pilot smoke
- production build

Smoke must verify:

- advisory label exists
- advisory surface is read-only
- no approval wording
- no clearance wording
- no override wording
- no task wording
- no patient messaging wording
- no acknowledgment action button

## Whitespace Gate

Required local check:

`git diff --check`

## No-Go Trigger

Any of these fail the gate:

- acknowledgment route appears
- acknowledgment DB table appears
- acknowledgment schema accepts positive decision, clearance or override flags
- UI adds approval, clearance or override action
- appointment status mutation appears in acknowledgment flow
- Task or Outcome Evidence appears
- patient messaging appears

## CI Decision

The repository CI should run targeted advisory and acknowledgment tests explicitly, even though they are also covered by the full backend suite.

Explicit targeted checks make safety regressions visible in CI logs.

