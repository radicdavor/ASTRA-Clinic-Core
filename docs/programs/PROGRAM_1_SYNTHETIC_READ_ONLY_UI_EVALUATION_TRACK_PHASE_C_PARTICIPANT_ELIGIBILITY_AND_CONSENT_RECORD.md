# Program 1 Phase C - Participant Eligibility and Consent Record

Status: blank controlled template.

## Session Identity

- Session ID: `[required]`
- Candidate commit SHA: `[required]`
- Session date/time/timezone: `[required]`
- Local machine identifier: `[required]`
- Moderator: `[required]`
- Observer/reviewer: `[optional]`
- Participant code: `[required; do not use a patient identifier]`

## Eligibility

Mark each item `YES`, `NO`, or `NOT CONFIRMED`:

- participant is an adult
- participant self-identifies as a clinician relevant to the intended review context
- participation is voluntary
- participation is not employment performance assessment
- participant understands the UI is synthetic-only
- participant agrees not to enter or disclose real patient or practice information
- participant understands this is not clinical validation or certification
- participant may stop at any time without consequence

Any `NO` or `NOT CONFIRMED` blocks the session.

## Consent Script

The moderator reads:

> This is a local synthetic demonstration. It contains no real patient data and must not be used for diagnosis, treatment, triage, patient communication, or clinical work. We are evaluating whether the interface and language are understandable, not evaluating you. Do not enter or describe information from a real patient or clinical case. You may pause or stop at any time. Your responses will be recorded only in the agreed session notes. Do you understand and voluntarily agree to continue?

## Consent Decision

- participant response: `[AGREE / DO NOT AGREE]`
- recording requested: `[NO by default / YES with separate explicit consent]`
- separate recording consent reference: `[required only if YES]`
- moderator signature/initials: `[required]`
- participant acknowledgment: `[required]`

If the participant does not agree, stop without opening the evaluation route.

