# Program 1 Phase C35 - Acknowledgment UI Action No-Go Hardening

Status: UI no-go hardening

## Purpose

C35 keeps the advisory surface read-only.

## Current UI Position

Appointment Workspace may show advisory signals.

It must not show:

- acknowledgment button
- approval button
- clearance button
- override button
- task button
- patient message button

## Forbidden Labels

- `Oznaci da je pregledano`
- `Evidentiraj pregled`
- `Approve`
- `Clear`
- `Override`
- `Create task`
- `Send message`

## Future Condition

Any future acknowledgment UI action requires:

- approved persistence model
- approved endpoint contract
- approved permission model
- approved audit event
- safety smoke coverage

## Runtime Status

No UI action is added in C35.

