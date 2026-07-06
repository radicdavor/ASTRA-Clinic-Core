# Codex master prompt v20 — ASTRA Workspace Architecture and Clinical Navigation Sprint

Use this prompt in Codex after V19 has been implemented.

---

You are a senior full-stack architect, healthcare workflow designer, and product consistency maintainer.

Before making changes, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md`
- `docs/CODEX_MASTER_PROMPT_V19.md`
- `docs/ASTRA_DESIGN_SYSTEM.md` if it exists

If `docs/ASTRA_DESIGN_SYSTEM.md` does not exist, stop and implement V19 first.

## Current assumption

V19 should have introduced:

- ASTRA Design System document
- ActionButton or equivalent action component
- consistent HelpHint rules
- centralized patient identity formatting
- improved patient duplicate awareness or explicit deferral
- better frontend smoke checks for action/help consistency

V20 must not undo that work.

## Sprint name

**Workspace Architecture and Clinical Navigation Sprint**

## Main goal

Move ASTRA from a collection of pages toward object-centered workspaces.

The first target is the **Patient Workspace**.

ASTRA must not feel like unrelated forms and tables. It should feel like a clinic operating system where every object has a clear workspace.

## Non-negotiable rules

- Do not enable real patient data.
- Do not implement real Croatian fiscalization.
- Do not add new broad clinical modules.
- Do not add AI receptionist or external integrations.
- Do not change Architecture Bible directly unless maintainer explicitly requests it.
- Preserve V19 action/help semantics.
- Keep patient identity rules consistent.
- Keep appointment create based on resolved `patient_id`.
- Keep demo warnings visible.

---

# Phase 1 — Create Workspace Architecture document

Create:

`docs/ASTRA_WORKSPACE_ARCHITECTURE.md`

This document defines how object-centered screens should work.

Required sections:

## 1. Why workspaces

Explain that clinic users think around objects:

- patient
- appointment
- invoice
- purchase order
- inventory item

Not around isolated forms.

## 2. Workspace definition

A workspace is a single object-centered screen that gathers:

- identity/header
- status
- primary actions
- related objects
- timeline/audit
- warnings
- next recommended actions

## 3. Standard workspace layout

Define zones:

1. Header/identity area
2. Status/action bar
3. Summary cards
4. Primary workflow panel
5. Related records tabs
6. Audit/timeline panel
7. Safety/demo warnings if relevant

## 4. Patient Workspace

Must include:

- patient identity
- OIB/date/phone/email display
- appointments
- invoices
- stock/material events related through appointments if feasible
- audit timeline
- notes
- duplicate warning if available
- create appointment action

## 5. Appointment Workspace

Already partly exists as AppointmentDetail.

Should include:

- patient identity
- service/provider/room/time
- status flow
- material consumption
- invoice link
- stock movements
- audit timeline

## 6. Invoice Workspace

Should include:

- invoice identity/status
- patient/appointment link
- lines
- payment history
- fiscalization status
- audit timeline

## 7. Inventory Item Workspace

Future standard:

- item identity
- current stock
- batches
- movements
- reorder status
- suppliers
- audit timeline

## 8. Purchase Order Workspace

Future standard:

- supplier
- status
- lines
- receiving workflow
- related stock movements
- audit timeline

Acceptance criteria:

- document exists
- linked from README and ASTRA Design System if available

---

# Phase 2 — Create shared Workspace components

Add reusable frontend components:

`frontend/src/components/workspace/WorkspaceLayout.tsx`
`frontend/src/components/workspace/WorkspaceHeader.tsx`
`frontend/src/components/workspace/WorkspaceSection.tsx`
`frontend/src/components/workspace/WorkspaceTabs.tsx` if useful
`frontend/src/components/workspace/StatusBadge.tsx` if no equivalent exists

Keep them simple.

They should standardize layout, not create heavy abstractions.

Acceptance criteria:

- Patient detail or AppointmentDetail uses at least WorkspaceLayout and WorkspaceHeader.
- Existing styles are not broken.

---

# Phase 3 — Implement Patient Workspace

Upgrade patient detail into a real Patient Workspace.

If current patient detail is minimal, create or improve:

`frontend/src/pages/PatientDetail.tsx`

Route:

`/patients/:id`

Must show:

- full patient identity using centralized patient identity helper
- OIB if present
- date of birth if present
- phone/email
- notes
- demo/real-data warning context if relevant
- appointments for this patient
- invoices for this patient if API supports it; otherwise document as deferred
- create appointment button prefilled or linked with patient context if practical
- audit timeline filtered to Patient entity
- possible duplicate warning if duplicate endpoint exists

Use ActionButton and HelpHint rules from V19.

Acceptance criteria:

- Patient list links to Patient Workspace.
- Patient Workspace is usable as the central patient object screen.

---

# Phase 4 — Strengthen Appointment Workspace

AppointmentDetail already exists. Refactor it toward the workspace pattern.

Must include or preserve:

- patient identity section with link to Patient Workspace
- appointment status and status action semantics
- material consumption panel
- invoice action/link
- stock movements
- audit timeline
- ActionButton for critical actions
- HelpHint where required

Acceptance criteria:

- AppointmentDetail looks and behaves as a workspace.
- No existing pilot flow is broken.

---

# Phase 5 — Add object backlinks

Improve navigation between related objects.

Add links:

- Appointment -> Patient Workspace
- Appointment -> Invoice Workspace or invoice list/details if available
- Invoice -> Appointment
- Invoice -> Patient
- Purchase receiving -> Inventory item if practical

If a target detail page does not exist, add TODO comments and documentation rather than building too much.

Acceptance criteria:

- User can navigate from appointment to patient and back to operational context.

---

# Phase 6 — API support for Patient Workspace

Add or reuse endpoints needed by Patient Workspace.

Preferred simple endpoints:

- `GET /api/patients/{id}` already exists
- `GET /api/appointments?patient=<name>` exists but is not ideal

Add better endpoint if needed:

`GET /api/patients/{patient_id}/appointments`

Optional:

`GET /api/patients/{patient_id}/invoices`

Do not overbuild.

Acceptance criteria:

- Patient Workspace can load patient appointments without fragile name search.

---

# Phase 7 — Workspace smoke tests

Update frontend smoke script to check:

- Workspace components exist
- PatientDetail/Patient Workspace exists
- route `/patients/:id` exists
- Patient list links to patient detail
- AppointmentDetail links to patient detail
- AppointmentDetail still contains material consumption workflow
- Demo/fiscalization warnings preserved

Backend tests if new endpoints are added:

- patient appointments endpoint returns only that patient appointments
- permission required for patient appointment endpoint

---

# Phase 8 — Documentation updates

Update:

- README — add link to Workspace Architecture
- `docs/ASTRA_DESIGN_SYSTEM.md` — link or mention Workspace Architecture
- `docs/PILOT_RUNBOOK.md` — update navigation steps if Patient Workspace added
- `docs/KNOWN_LIMITATIONS.md` — note any deferred workspace links
- `docs/V11_BACKLOG_FROM_PILOT.md` — mark patient workspace as addressed/in-progress if relevant

---

# Phase 9 — Architecture change proposal

Do not edit Architecture Bible directly.

Create:

`docs/ARCHITECTURE_CHANGE_PROPOSAL_WORKSPACES.md`

Propose adding to Architecture Bible:

- object-centered workspace principle
- Patient Workspace as primary object screen
- Appointment Workspace as operational workflow screen
- workspace layout zones
- cross-object navigation rules

---

# Suggested commit sequence

1. `docs: add workspace architecture specification`
2. `feat: add shared workspace layout components`
3. `feat: implement patient workspace`
4. `feat: align appointment detail with workspace pattern`
5. `feat: add patient appointment endpoint`
6. `feat: add cross-object navigation links`
7. `test: cover patient workspace endpoints and smoke checks`
8. `docs: update pilot and design docs for workspaces`
9. `docs: propose architecture bible workspace update`

---

# Definition of done

This sprint is done when:

- Workspace Architecture document exists and is linked.
- Basic workspace components exist.
- Patient Workspace exists at `/patients/:id`.
- Patient list links to Patient Workspace.
- AppointmentDetail links to Patient Workspace.
- Patient Workspace shows appointments through a safe patient-id endpoint or documented equivalent.
- AppointmentDetail still supports pilot material/invoice workflow.
- ActionButton/HelpHint standards from V19 remain intact.
- Frontend smoke covers workspace presence.
- Architecture Bible is not silently changed; proposal exists.

Do not add new modules, real fiscalization, integrations, real-data enablement, or new AI automation in this sprint.
