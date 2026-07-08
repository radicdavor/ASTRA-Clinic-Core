# Program 1 Phase C36 - Acknowledgment Persistence CI Gate

Status: CI gate documentation

## Purpose

C36 defines the regression checks that must remain active while acknowledgment persistence is no-go.

## Required Checks

- `git diff --check`
- backend compile
- targeted acknowledgment tests
- targeted advisory tests
- targeted snapshot tests
- full backend suite
- frontend typecheck
- frontend build
- frontend smoke

## Required Invariants

Tests must protect:

- no acknowledgment endpoint
- no acknowledgment DB model/table
- no acknowledgment seeded permissions
- reason-required passive schema
- no positive decision, clearance or override flags
- no forbidden UI action wording

## CI Status

The CI already runs targeted advisory and acknowledgment safety tests.

Future persistence work must add new targeted tests before adding runtime write behavior.

