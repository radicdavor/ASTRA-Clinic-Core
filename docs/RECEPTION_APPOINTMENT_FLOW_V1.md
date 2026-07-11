# Reception and Appointment Flow V1

Status: implemented.

## Purpose

This module shortens the core reception workflow while preserving patient identity and appointment safety:

`free reception slot -> new appointment -> arrival and identity verification -> start service`

## Implemented

- previous day, today, and next day controls in Reception
- compact half-hour empty-slot display instead of every ten-minute row
- existing appointments retain their exact start time, including 10- and 20-minute offsets
- every empty ten-minute slot links to New Appointment
- selected reception date and start time prefill the appointment form
- appointment time remains editable before creation
- arrival action is available only for scheduled or confirmed appointments
- arrival requires explicit identity verification
- UI requires first name, last name, and at least one additional identifier
- Start Service uses a dedicated API endpoint
- Start Service requires `arrived` status and recorded identity verification
- arrival and service start remain audited
- reception refreshes after workflow actions

## API

- existing: `POST /api/appointments/{appointment_id}/mark-arrived`
- new: `POST /api/appointments/{appointment_id}/start-service`

## Safety Boundaries

- no appointment for an unresolved patient
- no service start before arrival
- no service start without identity verification
- invalid state transitions return explicit 409 responses
- identity verification failure returns 422
- provider, room, service-duration, and overlap checks remain active during appointment creation

## Validation

- frontend typecheck
- frontend pilot smoke
- frontend production build
- 12 targeted backend appointment/reception tests
- Program 1 regression suite remains unchanged
