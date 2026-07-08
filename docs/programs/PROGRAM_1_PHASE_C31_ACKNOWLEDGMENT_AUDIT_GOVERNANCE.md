# Program 1 Phase C31 - Acknowledgment Audit Governance

Status: audit governance design

## Purpose

This document defines audit governance for future acknowledgment persistence.

C31 does not add a runtime audit event.

## Proposed Create Event

`clinical_readiness_advisory_review_acknowledged`

## Required Payload

- acknowledgment id
- appointment id
- patient id
- advisory signal key
- snapshot id if available
- actor user id
- actor role
- reason
- created at
- limitations
- `is_decision: false`
- `is_clearance: false`
- `is_override: false`

## Forbidden Payload

- approval status
- clearance status
- override status
- appointment status after
- task id
- outcome evidence id
- patient message id

## Audit Meaning

Audit means a review event occurred.

Audit does not mean:

- clinical approval
- readiness clearance
- override accepted
- task completed
- outcome documented
- patient notified

## Relationship To Existing Audit

Acknowledgment audit should use existing audit infrastructure.

It must not rewrite snapshot audit events or historical capture content.

