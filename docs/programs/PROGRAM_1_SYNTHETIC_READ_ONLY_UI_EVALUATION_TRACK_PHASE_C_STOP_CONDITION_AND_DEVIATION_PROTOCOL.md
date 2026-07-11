# Program 1 Phase C - Stop Condition and Deviation Protocol

Status: active for any future Phase C session.

## Immediate Stop Conditions

- real patient, appointment, institutional, or practice information is spoken, typed, shown, or suspected
- a participant attempts to use the UI for current clinical work
- diagnosis, treatment, triage, urgency, patient instruction, or clinical-clearance reliance occurs
- the participant withdraws consent or asks to stop
- candidate commit or scenario identity cannot be confirmed
- the UI exposes write, export, upload, messaging, appointment, or clinical writeback behavior
- local-only or synthetic-only boundaries cannot be confirmed
- recording begins without explicit separate consent
- moderator cannot explain or contain a deviation

## Stop Procedure

1. Say `Zaustavljamo evaluaciju.`
2. Prevent further entry or navigation.
3. Do not repeat sensitive information.
4. Close or isolate the affected screen.
5. Record only the minimum non-sensitive facts needed to classify the event.
6. Notify the named stop authority and decision owner.
7. Mark the session `STOPPED - NO EVALUATION DECISION`.
8. Require a new authorization before restart.

## Deviation Record

- Deviation ID:
- Session ID:
- Exact commit SHA:
- Date/time/timezone:
- Reporter:
- Observed behavior:
- Boundary affected:
- Real-data involvement: `[NO / SUSPECTED / YES]`
- Immediate containment:
- Evidence retained:
- Evidence deliberately not retained:
- Severity:
- Reviewer:
- Disposition:
- Reauthorization required: `[YES by default]`

A deviation is not permission to troubleshoot during the participant session.

