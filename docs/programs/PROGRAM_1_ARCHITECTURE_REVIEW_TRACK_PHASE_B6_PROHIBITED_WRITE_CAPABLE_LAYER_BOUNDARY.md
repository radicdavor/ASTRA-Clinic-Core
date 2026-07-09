# Program 1 Architecture Review Track Phase B6 - Prohibited Write-Capable Layer Boundary

Status: documentation-only prohibition record.

## Prohibited write-capable behavior

Write-capable behavior is prohibited in Phase B. This includes:

- Patient profile mutation.
- Appointment status mutation.
- Clinical note writing.
- Diagnosis writing.
- Treatment recommendation execution.
- Medication or instruction generation for patient delivery.
- Task creation or assignment.
- Outcome Evidence creation.
- Workflow enforcement.
- Approval/clearance/override execution.

## Related prohibited communication and scheduling paths

Phase B does not permit patient messaging, patient instructions, patient reminders, patient portal output, automated summaries to patients, direct patient communication, or indirect patient communication through staff workflow.

Phase B does not permit creating appointments, cancelling appointments, rescheduling appointments, changing appointment status, triage-driven scheduling mutation, automated queue movement, or operational scheduling enforcement.

## Current decision

All write-capable, communication-capable, appointment-capable, workflow-capable, Task engine, Outcome Evidence, and approval/clearance/override paths remain not approved, not cleared, not implemented, and not authorized.
