# Program 1 Phase C29 - Acknowledgment Migration Review

Status: migration review only

## Purpose

This document reviews what a future migration would need to protect.

C29 does not add an Alembic migration.

## Proposed Future Migration

Future migration may create:

`clinical_readiness_review_acknowledgments`

Only after maintainers approve persistence.

## Required Constraints

Future migration should include:

- non-empty reason check
- foreign key to appointment
- foreign key to patient
- nullable foreign key to snapshot
- foreign key to actor user
- immutable audit-friendly created timestamp
- no appointment status column
- no Task column
- no Outcome Evidence column
- no patient message column
- no approval, clearance or override columns

## Indexing

Future indexes may include:

- `appointment_id`
- `patient_id`
- `snapshot_id`
- `actor_user_id`
- `created_at`
- `advisory_signal_key`

## Rollback Strategy

Rollback must drop only the acknowledgment table and indexes.

Rollback must not affect snapshots, appointments, audit logs, patients or clinical documents.

## Risks

- persistence may be misread as approval
- users may expect an action button
- audit event naming may drift
- retention policy is not production-approved
- real-data use remains no-go

## Decision

Migration remains deferred.

No runtime persistence is implemented in C29.

