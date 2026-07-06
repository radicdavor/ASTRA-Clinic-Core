# ASTRA Design System

## Purpose

ASTRA Design System reduces cognitive load in clinic work. Its job is to make actions predictable, patient identity visible and critical workflow steps understandable without forcing users to read external manuals.

This design system implements the Architecture Bible principles: human above software, one shared language, contextual help, auditability and safety by default.

For object-centered screen structure, use `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`.

## Action Categories

- Information: reads or displays data without changing it.
- Create: creates a new object.
- Update: changes an existing object.
- Workflow: advances an operational process.
- Critical/danger: irreversible or hard-to-reverse change.
- AI-assisted: a suggestion or action initiated by an AI-controlled user.
- Admin/security: access, API keys, permissions or other security-sensitive actions.

## Standard Croatian Action Verbs

- Novi
- Dodaj
- Spremi
- Potvrdi
- Zavrsi
- Izdaj
- Evidentiraj
- Zaprimi
- Otpisi
- Deaktiviraj

Use these verbs consistently. Do not invent synonyms for the same action unless the domain meaning is truly different.

## HelpHint Rules

`HelpHint` is mandatory for:

- create actions
- critical actions
- financial actions
- inventory mutation
- API key actions
- identity-sensitive fields such as OIB

Help must be part of the UI. It must work on hover, focus and click/tap.

## Confirmation Rules

Require confirmation for:

- invoice issue
- payment recording
- appointment completion with material consumption
- purchase receiving
- stock write-off or adjustment
- API key deactivation

Critical actions must also be audited by the backend.

## Patient Identity Display

When showing a patient for selection or disambiguation, display:

- full name
- date of birth if available
- OIB if available
- phone or email if available

Never create an appointment for an unknown or unresolved patient.

## Demo And Fiscalization Warning Language

Demo warning:

> Demo mode is enabled. Do not enter real patient data.

Real-data warning:

> Real patient data is not allowed in this environment.

Fiscalization warning:

> Demo fiskalizacija - nije stvarna fiskalizacija.

## AI Label Language

AI output must be labeled as a suggestion or assistant action. AI must not be presented as a physician, administrator or responsible decision-maker.

Suggested label:

> AI prijedlog

AI may help organize, remind, analyze and speed up work. A human decides.

## Source Transparency

Clinical knowledge shown in Patient Workspace must link to source documents.

AI-assisted clinical statements without a source document must not be shown as official patient knowledge.

Unreviewed AI extraction is a pending proposal, not a clinical fact.
