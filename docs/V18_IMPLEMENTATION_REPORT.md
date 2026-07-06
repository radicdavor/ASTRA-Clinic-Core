# V18 Implementation Report

## Status

Implemented locally; GitHub CI must pass after push before `v0.1-pilot` can be tagged.

## Implemented

- Optional unique patient OIB field.
- OIB validation: exactly 11 digits when present.
- Patient search includes first name, last name, email, phone and OIB.
- Appointment creation now uses patient search/disambiguation and still submits a resolved `patient_id`.
- Service context card in appointment creation.
- `HelpHint` popover component for hover, focus and click/tap help.
- Contextual help on patient creation, appointment creation, services, material completion, draft invoice, invoice issue, payment, purchase receiving and API key actions.
- Demo/OIB documentation updates.
- Frontend smoke checks for OIB, patient search and help hints.
- Backend tests for OIB create, validation, duplicate rejection and search.

## Boundaries Preserved

- `docs/ASTRA_ARCHITECTURE_BIBLE.md` now records the founder-level product philosophy and architecture principles.
- Real patient data remains forbidden.
- Real OIB values must not be entered in demo mode.
- Real Croatian fiscalization is still not implemented.
- Appointment create still requires a resolved `patient_id`.
- No new clinical modules, AI automations or external integrations were added.

## CI Fix Included

Migration `0004_fiscalization_metadata` was made idempotent because GitHub CI was failing on duplicate invoice fiscalization columns during migration replay.
