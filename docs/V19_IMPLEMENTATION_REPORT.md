# V19 Implementation Report

## Scope

V19 implements the ASTRA Design System and UX consistency sprint from `docs/CODEX_MASTER_PROMPT_V19.md`.

## Completed

- Added `docs/ASTRA_DESIGN_SYSTEM.md`.
- Added reusable `ActionButton` for categorized UI actions, contextual help and confirmations.
- Applied `ActionButton` to patient creation, appointment creation, appointment completion with material consumption, invoice issue, payment recording, purchase receiving and API key actions.
- Added `frontend/src/utils/patientIdentity.ts` for one patient identity language.
- Added `GET /api/patients/possible-duplicates`.
- Added possible-duplicate warning before saving a new patient.
- Added backend test coverage for duplicate candidate lookup.
- Added architecture change proposal for patient identity and action-language rules.

## OIB Decision

OIB checksum validation remains deferred for pilot. Current validation only checks the 11-digit shape. Real OIB entry remains prohibited until real-data readiness is approved.

## Architecture Bible Check

- Human above software: users get clearer context before critical actions.
- One source of truth: patient identity formatting is centralized.
- One language: action categories and verbs are documented.
- Modular Clinic Core: no new medical module or EMR scope was added.
- API First: duplicate lookup is available through REST.
- Audit and safety: critical actions keep backend audit behavior and add consistent confirmation.
