# Program 1 Phase C108 - Acknowledgment Sensitive Read Boundary

Status: sensitive read boundary

## Purpose

C108 defines when acknowledgment read access should be considered sensitive.

## Sensitive Read Criteria

Sensitive read criteria include:

- detail read of a specific acknowledgment record
- denied read attempt
- cross-appointment access attempt
- patient mismatch attempt
- API key read attempt
- AI/system read attempt
- bulk/list access pattern that is unusual for the role

## Role-Based Sensitivity

Physician/admin read in demo/pilot may be expected.

Nurse/reception read may be limited by permission design.

API key, AI agent and system job reads are sensitive and should be denied by default for acknowledgment read surfaces.

## Cross-Appointment Access

Any attempt to read an acknowledgment through the wrong appointment context is sensitive.

Audit payload must not leak whether the acknowledgment exists elsewhere.

## Patient Mismatch Attempts

Patient mismatch is sensitive because it can indicate access boundary confusion or a privacy issue.

## Detail Reads

Detail reads are more sensitive than list reads because they target a specific record.

Detail success audit remains deferred until noise/privacy decisions are complete.

## Denied Reads

Denied reads are the preferred first candidate for future runtime audit.

## Bulk/List Reads

List reads should not be automatically considered suspicious.

They become sensitive when volume, role or timing is unusual.

## Audit Escalation Criteria

Escalation may be considered when:

- repeated denied reads occur
- API key or AI/system actor attempts read
- cross-appointment attempts repeat
- access pattern does not match role expectations

## Privacy and Security Implications

Sensitive read audit must be privacy-minimized.

It must avoid clinical reason text and must not create clinical evidence semantics.

## Production Boundary

C108 does not approve production or real patient data use.

