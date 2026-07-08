# Program 1 Phase D36 - Findings Read Service Contract

Status: service/helper contract

## Purpose

Define a side-effect-free read boundary for persisted findings.

## Required Behavior

Read helpers must support:

- patient-scoped list
- patient-scoped detail
- optional future appointment-context filtering
- source-linked response mapping
- lifecycle status filtering
- requires review filtering
- newest-first sorting
- empty list state
- not-found and out-of-scope behavior

## Side-Effect Boundary

Read helpers must not:

- write audit events by default
- mutate patient, appointment or finding records
- create Tasks
- create Outcome Evidence
- send patient messages
- change appointment status
- diagnose or treat
- approve, clear or override

## Implementation Note

For a narrow prototype, route-local read mapping is acceptable if it remains small and side-effect-free.

