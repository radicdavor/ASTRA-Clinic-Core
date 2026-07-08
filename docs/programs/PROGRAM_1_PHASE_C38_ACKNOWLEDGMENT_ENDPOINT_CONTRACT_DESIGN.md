# Program 1 Phase C38 - Acknowledgment Endpoint Contract Design

Status: endpoint contract only

## Purpose

This document defines a future endpoint contract for Human Review Acknowledgment.

C38 does not implement a route.

## Proposed Future Route

`POST /api/appointments/{appointment_id}/clinical-readiness-acknowledgments`

## Scope

The future endpoint would record that a permitted human reviewed an advisory signal in appointment context.

It must not:

- approve a procedure
- clear readiness
- override readiness
- change appointment status
- create a Task
- create Outcome Evidence
- send a patient message

## Preconditions

Future implementation would require:

- approved persistence model
- approved migration
- approved permission model
- approved audit event
- approved UI wording
- regression tests

## Runtime Boundary

No endpoint is implemented in C38.

Runtime acknowledgment remains no-go.

