# Program 1 Phase B33 - Snapshot Audit Export Contract

Status: design-only audit export contract

## Purpose

This document defines the safe export contract for Clinical Readiness Snapshot audit review in demo/pilot context.

It does not add a new endpoint.

## Current Read Pattern

ASTRA already has a read-only Audit Log surface and backend route that can filter audit logs.

Snapshot audit export should use existing audit read patterns before any new export endpoint is considered.

## Allowed Export Fields

Allowed fields:

- audit event id
- created timestamp
- actor type
- actor user id
- actor API key id if present
- action
- entity type
- entity id
- summary
- before/after JSON payload
- snapshot id
- appointment id
- patient id
- service id/name
- capture or supersession reason
- template metadata
- preview status and summary

## Forbidden Export Fields

Export must not add or imply:

- clinical approval
- readiness clearance
- procedure permission
- override acceptance
- Outcome Evidence id
- Task id
- patient message status
- clinical enforcement status

## Demo/Pilot Only

Snapshot audit export is demo/pilot only until maintainers approve:

- real-data policy
- access-control review
- legal/compliance wording
- audit retention policy
- backup/restore drill
- incident response procedure

## No Patient Messaging

Export must not send messages to patients.

Export is an operator review artifact, not a patient communication feature.

## No Clinical Decision Export

Export may show what preview was saved and why.

Export must not claim that:

- the patient was ready
- a procedure was approved
- a warning was cleared
- a physician made a final clinical decision through snapshot state

## Relationship To Retention

Export is secondary to retention.

If audit retention is incomplete, export is incomplete.

Export must not be used to compensate for deleted or missing audit rows.

## Relationship To Restore

After restore, export must be validated against:

- snapshot rows
- audit rows
- supersession relationships
- immutable trigger presence

## Production Status

No production readiness is claimed.

## Recommended Next Task

`Program 1 Phase B34 - Snapshot Backup and Restore Consistency Runbook`
