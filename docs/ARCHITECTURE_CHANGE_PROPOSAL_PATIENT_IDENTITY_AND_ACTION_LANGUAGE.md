# Architecture Change Proposal: Patient Identity And Action Language

## Status

Proposed for maintainer review.

## Proposed Bible Addition

Add an explicit subsection under `Identitet pacijenta`:

- Patient selection screens must show full name plus at least one available disambiguator: date of birth, OIB, phone or email.
- Appointment creation must use a resolved patient record, not free-text identity.
- If a possible duplicate exists, the user must confirm they reviewed the identity before creating a new patient.

Add an explicit subsection under `Pravila dizajna`:

- Repeated action types must use the same Croatian verbs across the platform.
- Critical actions must use a consistent confirmation pattern and contextual help.
- Financial, inventory, appointment-completion and API-key actions are critical unless explicitly classified otherwise.

## Why This Is Needed

V18 exposed patient identity ambiguity as a safety risk. V19 exposed action-language inconsistency as a usability risk: users had difficulty noticing whether patient entry, payment and similar actions were completed.

Both issues are already implied by the Architecture Bible, but they are important enough to become explicit rules.

## Current Implementation

- `docs/ASTRA_DESIGN_SYSTEM.md` defines the operational design-system rules.
- `frontend/src/utils/patientIdentity.ts` centralizes patient identity formatting.
- `frontend/src/components/ActionButton.tsx` centralizes action category, help and confirmation behavior.
- `/api/patients/possible-duplicates` supports duplicate checks before new patient creation.

## Risk If Not Clarified

Without an explicit rule, future modules may use different labels for the same action, hide patient identity details, or allow risky changes without consistent confirmation. That would weaken the shared ASTRA language and increase cognitive load for clinic staff.
