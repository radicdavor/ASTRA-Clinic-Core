# Production Safety Foundation — Phase E Clinic Timezone Policy

## Status

Implemented as an incremental backend foundation. This does not close the full Production Safety Foundation track.

## Canonical policy

Clinic scheduling uses the clinic's local civil day.

For ASTRA's current clinic context, the default IANA timezone is:

```text
Europe/Zagreb
```

Each clinic stores its timezone on `clinics.timezone`.

## Storage rules

Appointment planning fields remain clinic-local:

- `appointments.date`
- `appointments.start_time`
- `appointments.end_time`

Event/audit timestamps remain timezone-aware instants:

- `created_at`
- `updated_at`
- `arrived_at`
- `reviewed_at`
- `signed_at`
- other operational timestamps

These timestamp fields represent absolute time and should be generated as UTC-aware datetimes where application code controls the value.

## Local day rule

When the backend needs "today for this clinic", it must compute it from the clinic timezone, not from browser UTC serialization.

Use:

```python
clinic_local_date(clinic.timezone)
```

## DST rule

For DST transitions, the clinic-local date is determined by converting a timezone-aware instant into the clinic timezone first, then taking `.date()`.

ASTRA does not currently support appointments that span midnight or ambiguous wall-clock times during DST transitions. If that becomes necessary, appointment storage must be revisited with explicit timezone-aware start/end instants.

## Frontend rule

The frontend may display and submit clinic-local dates such as `dd. mm. yyyy.` or `YYYY-MM-DD`, but must not derive clinic day by taking `toISOString().slice(0, 10)` from a local `Date` object.

Frontend date helper cleanup remains a follow-up task.
