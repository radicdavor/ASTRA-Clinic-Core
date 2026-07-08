# Program 1 Phase C107 - Acknowledgment Read Audit Noise Control Policy

Status: noise control policy

## Purpose

C107 documents how ASTRA should avoid making acknowledgment read audit unusable through excessive events.

## Risk of Logging Every List Refresh

Appointment Workspace can fetch acknowledgment lists during page load and later refreshes.

Auditing every list read would create high-volume low-signal audit records.

## Repeated Polling and Refresh Risk

If future UI refresh, polling or tab restore behavior re-requests the list, audit count may grow without meaningful user intent.

## Frontend Re-render Risk

Frontend state changes must not create repeated audit events unless an intentional read action occurred.

## Detail Read vs List Read Threshold

Detail read has higher signal than list read because a user requests a specific record.

Even so, detail success audit remains deferred until:

- privacy payload is approved
- audit review workflow exists
- retention/export rules are reviewed

## When Not To Audit

Do not audit by default:

- normal list read during Appointment Workspace load
- passive frontend render
- retries caused by transient network behavior
- local UI state changes

## When To Audit Denied Access

Denied access is higher value because it can show:

- missing permission attempts
- API key access attempts
- non-human actor attempts
- out-of-scope appointment attempts

## Unusual Access

Future unusual access audit may consider:

- repeated denied reads
- repeated cross-appointment attempts
- high-frequency detail reads
- access by unexpected role

## Rate-Limit or Sampling Considerations

If success-read audit is ever implemented, ASTRA should consider:

- per-user throttling
- per-appointment throttling
- sampling list reads
- logging only explicit detail opens

## Implementation Position

No implementation in C107.

Denied-read audit may be considered first.

List read audit should remain cautious and deferred.

