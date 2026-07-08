# Program 1 Phase D117 - Open Question Read API CI Gate

Status: documented

## Gate Scope

The open question read API contract gate must include:

- open question contract and passive schema tests
- open question persistence tests
- read-contract no-go route and service absence guards
- clinical finding extraction contract tests
- findings lifecycle, persistence and read API tests
- acknowledgment and snapshot regression tests
- full backend suite
- frontend typecheck, build and smoke

## Current CI Decision

No new CI dependency or workflow step is added in this phase. The full backend suite already exercises the open question contract and persistence tests, and the required end-of-phase manual gate remains explicit until a later endpoint prototype exists.

## Runtime Boundary

The CI gate is verification only. It does not add an endpoint, service, permission seed, frontend client, UI action, audit write or automatic question creation.

## No-Go Assertions

The gate must continue to fail if a later change accidentally introduces:

- open question GET endpoint before approval
- open question POST, PATCH, PUT or DELETE endpoint
- review, approve, clear or resolve endpoint
- Task, Outcome Evidence or patient messaging behavior
- diagnosis, treatment, approval, clearance or override semantics
