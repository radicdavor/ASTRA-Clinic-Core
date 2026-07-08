# Program 1 Phase C49 - Acknowledgment Migration Draft Design

Status: migration draft design

## Purpose

This document defines the acknowledgment persistence migration draft.

The migration is DB foundation only.

It does not approve runtime endpoint, service, frontend action, production use or real patient data.

## Table Name

`clinical_readiness_review_acknowledgments`

## SQLAlchemy Model Name

`ClinicalReadinessReviewAcknowledgment`

## Alembic Revision Intent

Create a passive persistence table for future human review acknowledgment records.

## Columns

- `id`
- `appointment_id`
- `patient_id`
- `snapshot_id`
- `advisory_signal_key`
- `actor_user_id`
- `actor_role`
- `reason`
- `limitations_json`
- `schema_version`
- `not_decision_disclaimer`
- `is_decision`
- `is_clearance`
- `is_override`
- `created_at`

## Constraints

- reason must be non-empty
- `is_decision` must be false
- `is_clearance` must be false
- `is_override` must be false

## Indexes

Indexes are expected for:

- appointment
- patient
- snapshot
- advisory signal key
- actor user
- actor role
- created timestamp

## Foreign Keys

Expected references:

- appointment
- patient
- snapshot when available
- actor user

## Immutable Field Expectations

Future service design should treat all acknowledgment fields as immutable after insert.

Correction should be additive, not destructive.

## Downgrade Expectations

Downgrade may drop only the acknowledgment table and indexes.

It must not alter snapshots, appointments, patients, audit logs or clinical documents.

## Test Expectations

Tests must prove:

- model/table shape
- forbidden workflow fields absent
- false-only safety constraints exist
- endpoint remains absent
- frontend write client remains absent
- permission seed remains absent

## Runtime Boundary

No endpoint.

No write service.

No frontend action.

No production or real-data approval.

