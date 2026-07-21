# ADR: Date and Time Policy

## Status

Accepted for the Production Safety Foundation.

## Rules

1. Clinic date means the calendar date in the active clinic's IANA timezone.
2. Event timestamps are stored as timezone-aware UTC datetimes.
3. API datetime values must include `Z` or an explicit offset.
4. API date values remain plain `YYYY-MM-DD`.
5. Every clinic has a valid IANA timezone. The default is `Europe/Zagreb`.
6. Browser timezone is not the source of truth for clinic-local today.
7. Server local timezone is not the source of truth for clinic-local today.
8. Frontend critical flows must not use `new Date().toISOString().slice(0, 10)` to derive clinic-local today.
9. Backend critical timestamps must not use naive `datetime.now()`.
10. `datetime.combine(date, time)` must be interpreted explicitly as clinic-local when it represents scheduling time.

## Scheduling intervals

ASTRA currently models appointments as one clinic-local date with start and end wall-clock times. The current production rule is:

- an appointment must end after it starts;
- an appointment is expected to finish on the same clinic-local date;
- overnight appointments are not supported by this model.

The scheduling validator interprets date/time pairs in the room or provider clinic timezone before calculating real elapsed duration.

## DST policy

For clinic-local appointment time:

- nonexistent spring-DST local times are rejected;
- ambiguous autumn-DST local times are rejected;
- ASTRA does not silently shift or guess wall-clock time.

This is intentionally conservative. If the business later needs overnight or DST-boundary scheduling, the data model should move to full start/end datetimes with explicit offsets.

## Frontend policy

Frontend critical date defaults use `getClinicToday(timeZone)` from the active clinic context. If clinic context is unavailable, the safe fallback is `Europe/Zagreb`.

The browser may format display timestamps, but only with an explicit clinic timezone for clinic-operational views such as the daily dashboard.
