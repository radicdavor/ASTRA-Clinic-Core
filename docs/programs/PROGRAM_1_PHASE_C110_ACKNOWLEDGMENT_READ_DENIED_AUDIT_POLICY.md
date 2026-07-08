# Program 1 Phase C110 - Acknowledgment Read Denied Audit Policy

Status: denied-read audit policy

## Purpose

C110 defines the preferred selective audit policy for denied acknowledgment read attempts.

This is policy documentation only.

## When Denied Access Should Be Audited

Future denied-read audit should be considered when:

- authenticated user lacks `clinical_readiness.acknowledgments.read`
- API key attempts acknowledgment read
- AI agent or system actor attempts acknowledgment read
- request targets an appointment outside actor scope
- request targets an acknowledgment outside the appointment context
- repeated denied attempts occur

## API Key Denied Behavior

API keys should remain denied for acknowledgment read.

If denied-read audit is implemented later, payload may include a safe API key identifier, but must not leak clinical content.

## AI Agent and System Job Denial

AI agent, system job and automated actor reads should be denied by default.

Denied-read audit may record actor type and safe request context.

## Missing Permission

Missing permission is the primary denied-read audit case.

The audit payload should include:

- actor user id if available
- appointment id if safely resolved
- access type
- result: `denied`
- safe category: `missing_permission`

## Invalid Appointment

Invalid appointment should use a privacy-safe category.

Audit must avoid exposing whether patient or acknowledgment data exists elsewhere.

## Out-of-Scope Acknowledgment

Out-of-scope acknowledgment access should be denied without revealing cross-appointment existence.

Future audit may record:

- requested appointment id
- requested acknowledgment id
- safe category: `appointment_scope_mismatch`

## Privacy-Safe Denial Payload

Denied payload must not include:

- full reason text
- clinical note content
- approval/clearance/override state
- Outcome Evidence link
- Task link
- patient message link

## User-Facing Message Boundary

User-facing denial text should remain local and neutral.

It must not say:

- approval denied
- clearance denied
- override denied
- patient blocked
- patient not ready

## Workflow Boundary

Denied-read audit must not mutate:

- appointment status
- Task
- Outcome Evidence
- patient messaging
- clinical decision state

## Implementation Position

Denied-read audit is the recommended future runtime prototype.

Normal list/detail success-read audit remains deferred.

