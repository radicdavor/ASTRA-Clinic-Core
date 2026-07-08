# Program 1 Phase C13 - Enforcement Readiness CI Gate

Status: CI/test gate design

## Purpose

This gate defines checks needed before future Clinical Readiness work proceeds.

## Required Gate

- snapshot tests
- advisory signal schema tests
- forbidden wording smoke
- frontend typecheck
- frontend build
- frontend smoke
- full backend suite
- migration upgrade
- diff check

## Existing CI

Existing CI already runs:

- migrations
- targeted snapshot tests
- full backend tests
- frontend typecheck
- frontend smoke
- frontend build

## Advisory Signal Tests

C6-C8 add advisory signal schema tests.

These are included in the full backend suite.

## No Duplicate CI Step

No separate advisory-only CI step is added in C13 to avoid unnecessary duplication.

## Recommended Next Task

`Program 1 Phase C14 - Phase C Enforcement Readiness Go/No-Go Matrix`
