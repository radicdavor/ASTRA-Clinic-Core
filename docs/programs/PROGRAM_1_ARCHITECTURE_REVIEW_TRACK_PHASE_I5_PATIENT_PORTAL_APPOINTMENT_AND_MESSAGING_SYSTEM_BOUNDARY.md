# Program 1 Architecture Review Track Phase I5 - Patient Portal, Appointment, and Messaging System Boundary

Status: documentation-only, synthetic-only, non-runtime external system boundary.

Patient portal, appointment system, and messaging system boundaries are future conceptual dependencies only.

## Patient portal

Phase I5 prohibits patient portal connectors, patient account access, portal message reads/writes, form imports, file ingestion, and patient instruction delivery.

## Appointment system

Phase I5 prohibits appointment system connectors, appointment synchronization, appointment mutation, appointment status changes, scheduling writes, and workflow enforcement.

## Messaging system

Phase I5 prohibits patient messaging, staff messaging integration, notification delivery, message ingestion, message export, queue-based delivery, and alerting integration.

## Decision

No patient portal, appointment system, or messaging system access or mutation is approved.
