# Program 1 Phase D67 - Extraction Candidate Boundary Contract

Status: boundary contract

## Purpose

Define candidate finding as temporary, unofficial source-linked structure.

## Candidate Finding

A candidate finding may be proposed from ClinicalDocument source context.

It is not:

- persisted finding
- diagnosis
- recommendation
- physician decision
- patient instruction
- Task
- Outcome Evidence
- patient message
- approval, clearance or override

## Required Fields

Every candidate must include:

- candidate key
- label
- category
- source reference
- limitations
- human review requirement
- suggested safe lifecycle status

## Source Boundary

A candidate without source reference is invalid for persistence and must not be displayed as final truth.

## Review Boundary

A candidate may require human review. Human review must occur before persistence or clinical interpretation under a future policy.

## No Automatic Effects

Candidate creation must not create tasks, outcome evidence, patient messages, appointment status changes, treatment plans or diagnosis records.

