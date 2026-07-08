# Program 1 Phase C51 - Acknowledgment DB Shape Guardrails

Status: DB shape guardrails

## Purpose

C51 documents the guardrails for the new passive acknowledgment DB foundation.

## Required Columns

The table may contain only review-context fields:

- appointment reference
- patient reference
- snapshot reference
- advisory signal key
- actor metadata
- reason
- limitations
- schema version
- non-decision disclaimer
- false-only safety flags
- created timestamp

## Forbidden Columns

The table must not contain:

- approval status
- clearance status
- override status
- outcome evidence id
- task id
- patient message id
- appointment status
- procedure approved
- patient ready
- resolved timestamp

## Constraint Guardrails

The DB foundation must enforce:

- non-empty reason
- `is_decision = false`
- `is_clearance = false`
- `is_override = false`

## Runtime Boundary

DB shape does not approve endpoint, service or UI action implementation.

