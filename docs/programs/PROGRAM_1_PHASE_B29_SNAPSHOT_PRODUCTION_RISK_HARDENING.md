# Program 1 Phase B29 - Snapshot Production Risk Hardening

Status: production-risk hardening plan for Clinical Readiness Snapshot

## Purpose

Phase B29 is a hardening phase after the snapshot closure gate.

It does not expand Clinical Readiness Snapshot behavior. It defines the production-risk work that must be completed before any future clinical enforcement, production use, or real-patient-data decision.

## Current Baseline

The snapshot subphase is closed for demo/pilot use with guardrails:

- live preview exists
- snapshot capture exists
- snapshot history exists
- snapshot detail read exists
- snapshot idempotency exists
- supersession service exists
- supersession endpoint exists
- reason-required supersession UI exists
- regression and smoke coverage exist
- closure/go-no-go/next-step documents exist

The system remains explicitly not production-ready.

## Scope

B29 covers:

- DB-level immutability trigger design
- production no-go gate definition
- real-data no-go reinforcement
- audit review expectations
- backup/restore implications
- permission UX risk review
- CI/regression gate expectations
- legal/compliance disclaimer expectations

## Non-Scope

B29 must not implement:

- clinical approval
- readiness clearance
- override workflow
- Outcome Evidence
- Task engine
- appointment status change
- patient messaging
- clinical enforcement
- real AI/OCR
- real patient data approval
- production/certification claims

## Required Production-Risk Questions

Before ASTRA can move toward production or clinical enforcement, maintainers must answer:

1. Can historical snapshot payloads be technically protected from UPDATE and DELETE at the database layer?
2. What actor is allowed to create or supersede snapshots in production?
3. How will audit events be reviewed, exported, retained, and restored?
4. How will backup/restore preserve snapshot/audit consistency?
5. What wording is legally safe for users who see warning, not-ready, and superseded states?
6. How will permission failures be explained without implying hidden clinical clearance?
7. What CI checks must block merge before production deployment?
8. What documented review is required before real patient data can be entered?

## Hardening Principles

### Additive History

Supersession remains additive. A new snapshot may mark an older snapshot as superseded, but the old copied payload must remain unchanged.

### No Runtime Enforcement

Snapshot state must not block, approve, clear, reschedule, close, or message anything.

### Human Interpretation

The UI may show captured readiness context. It must not present the result as a clinical decision.

### Audit Completeness

Capture and supersession audit events must remain sufficient to reconstruct who created the snapshot, why, which appointment it belonged to, and what relationship exists between old and new snapshots.

### Production Skepticism

Demo/pilot safety does not imply production safety. B29 treats production as no-go until explicit later review.

## Recommended B29 Deliverables

- DB immutability trigger design document
- production risk go/no-go gate
- regression notes for B29
- README/roadmap pointers to B29 status
- later implementation candidate for DB trigger migration and regression tests

## Acceptance Criteria

B29 is acceptable only if it:

- reinforces that real patient data remains no-go
- reinforces that clinical enforcement remains no-go
- identifies DB-level immutability as a production blocker until implemented and tested
- keeps snapshot supersession additive
- keeps old snapshot payload unchanged
- does not add new runtime behavior

## Recommended Next Step After B29

If maintainers want code hardening next:

`Program 1 Phase B30 - Snapshot DB Immutability Trigger Prototype`

If maintainers want governance hardening next:

`Program 1 Phase B30 - Snapshot Production Governance Runbook`

Do not start Clinical Readiness enforcement until B29/B30 risks are explicitly closed.
