# Codex master prompt v19 — ASTRA Design System and UX Consistency Sprint

Use this prompt in Codex for the next sprint of `radicdavor/ASTRA-Clinic-Core`.

Before changing code, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md`
- `docs/V18_PATIENT_IDENTITY_AND_CONTEXTUAL_HELP_PLAN.md`

The Architecture Bible is the highest architecture reference. Do not change it directly unless the maintainer explicitly asks for that exact edit.

## Current state after V18

V18 implemented important patient identity and usability improvements:

- Patient has optional `oib` field.
- Patient schemas validate OIB as 11 digits when present.
- Patient search includes first name, last name, phone, email and OIB.
- AppointmentForm uses patient search and a selected-patient card instead of only a raw dropdown.
- HelpHint component exists.
- PatientForm includes OIB and help text.
- AppointmentForm shows service context.

This sprint should not add broad new product scope. It should make these improvements consistent across the application.

Sprint name:

**ASTRA Design System and UX Consistency Sprint**

## Main objective

Make action language, contextual help, patient identity display, and critical workflow buttons consistent across ASTRA.

## Rules

- Keep OIB optional.
- Keep appointment creation based on resolved `patient_id`, not free text.
- Do not add new clinical modules.
- Do not add new integrations.
- Do not add new AI automation.
- Do not implement real fiscalization in this sprint.
- Preserve demo warnings and current safety language.
- Keep changes focused on consistency, usability, and tests.

## Phase 1 — Add ASTRA Design System document

Create:

`docs/ASTRA_DESIGN_SYSTEM.md`

Include:

1. Purpose: reduce cognitive load in clinic work.
2. Action categories:
   - information
   - create
   - update
   - workflow
   - critical/danger
   - AI-assisted
   - admin/security
3. Standard Croatian action verbs:
   - Novi
   - Dodaj
   - Spremi
   - Potvrdi
   - Završi
   - Izdaj
   - Evidentiraj
   - Zaprimi
   - Otpiši
   - Deaktiviraj
4. When HelpHint is mandatory:
   - create actions
   - critical actions
   - financial actions
   - inventory mutation
   - API key actions
   - identity-sensitive fields such as OIB
5. Confirmation rules:
   - invoice issue
   - payment recording
   - appointment completion with material consumption
   - purchase receiving
   - stock write-off/adjustment
   - API key deactivation
6. Patient identity display rules:
   - full name
   - date of birth if available
   - OIB if available
   - phone/email if available
7. Demo and fiscalization warning language.
8. AI label language, without adding new AI features.

Link this document from README and from Codex instructions.

## Phase 2 — Add reusable ActionButton component

Create:

`frontend/src/components/ActionButton.tsx`

Props:

- `variant`: `info | create | update | workflow | danger | ai | admin`
- `helpTitle?: string`
- `help?: ReactNode`
- `requiresConfirm?: boolean`
- `confirmMessage?: string`
- `disabled?: boolean`
- `type?: "button" | "submit"`
- `onClick?: () => void | Promise<void>`
- `children`

Behavior:

- renders a button with consistent class names
- renders HelpHint when help is provided
- if `requiresConfirm`, ask for confirmation before action
- support submit buttons
- keep implementation simple

## Phase 3 — Apply ActionButton to high-risk workflows

Use ActionButton or an equivalent pattern in:

- PatientForm — Spremi pacijenta
- AppointmentForm — Spremi termin
- AppointmentDetail — Završi uz potrošnju
- Invoices — Izdaj račun
- Invoices — Evidentiraj uplatu
- PurchaseOrders — Potvrdi zaprimanje
- ApiKeys — Kreiraj API ključ
- ApiKeys — Deaktiviraj API ključ

Do not redesign the whole UI.

## Phase 4 — Centralize patient identity formatting

Create:

`frontend/src/utils/patientIdentity.ts`

Functions:

- `formatPatientName(patient)`
- `formatPatientIdentity(patient)`
- `hasStrongPatientIdentifier(patient)`

Use these in:

- AppointmentForm patient results
- selected patient card
- AppointmentDetail patient section
- patient list/detail if practical

## Phase 5 — Add lightweight duplicate awareness

Do not implement full patient merge.

Add endpoint:

`GET /api/patients/possible-duplicates`

Inputs:

- first_name
- last_name
- date_of_birth
- phone
- email
- oib

Rules:

- OIB duplicate remains blocking through uniqueness.
- Possible duplicate by name plus date/phone/email returns warning candidates.
- Do not block create unless OIB duplicate exists.

PatientForm:

- before submit or after enough fields, show possible duplicate warning
- show candidate identity details
- allow continue after explicit confirmation

## Phase 6 — Clarify OIB validation

Current validation checks 11 digits.

Either:

- add Croatian OIB checksum validation with tests, or
- document that checksum validation is deferred.

Do not overcomplicate.

## Phase 7 — Tests and smoke checks

Backend tests:

- create patient without OIB
- create patient with valid OIB
- reject invalid OIB
- reject duplicate OIB
- search by OIB
- possible duplicates endpoint

Frontend smoke/static checks:

- HelpHint exists
- ActionButton exists
- PatientForm contains OIB help
- AppointmentForm contains patient search input
- AppointmentForm selected patient card exists
- AppointmentForm submit disabled until patient selected
- Invoices still show demo fiscalization warning
- ApiKeys still show dangerous scope confirmation

## Phase 8 — Update documentation and pilot traceability

Update:

- `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`
- `docs/V11_BACKLOG_FROM_PILOT.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/PILOT_RUNBOOK.md`
- `docs/REAL_DATA_READINESS_CHECKLIST.md`

Mark this feedback as:

- Severity: P2
- Area: patient identity / UX
- Finding: contextual help and safer patient selection were requested during human walkthrough.
- Status: addressed or in-progress.

## Phase 9 — Architecture change proposal

Do not edit the Architecture Bible directly.

Create:

`docs/ARCHITECTURE_CHANGE_PROPOSAL_PATIENT_IDENTITY_AND_ACTION_LANGUAGE.md`

Propose future Bible additions:

- formal patient identity rules
- standard action verbs
- HelpHint requirement
- critical action confirmation rule
- duplicate awareness principle

## Suggested commit sequence

1. `docs: add ASTRA design system specification`
2. `feat: add reusable action button component`
3. `feat: apply action button to critical workflows`
4. `feat: centralize patient identity formatting`
5. `feat: add patient duplicate awareness endpoint`
6. `feat: warn about possible duplicate patients in form`
7. `test: cover OIB and duplicate workflows`
8. `test: harden frontend smoke for action help consistency`
9. `docs: trace patient identity feedback to pilot triage`
10. `docs: propose architecture bible identity and action language update`

## Definition of done

- Design system document exists and is linked.
- ActionButton exists.
- High-risk actions use ActionButton or equivalent.
- Patient identity formatting is centralized.
- Appointment patient search remains resolved-patient-only.
- Duplicate warning exists or is explicitly deferred.
- OIB behavior is tested and documented.
- Frontend smoke covers HelpHint/ActionButton/patient search basics.
- Pilot triage records this feedback.
- Architecture Bible is not silently changed.
