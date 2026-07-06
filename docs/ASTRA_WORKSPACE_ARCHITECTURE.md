# ASTRA Workspace Architecture

## 1. Why Workspaces

Clinic staff think around objects, not isolated forms.

Core ASTRA objects are:

- patient
- clinical episode
- appointment
- invoice
- purchase order
- inventory item

A workspace gathers the operational context around one object so the user can understand what is happening without jumping through unrelated screens.

## 2. Workspace Definition

A workspace is a single object-centered screen that gathers:

- identity/header
- status
- primary actions
- related objects
- timeline/audit
- warnings
- next recommended actions

It is a UI structure, not a new medical module.

## 3. Standard Workspace Layout

Workspace screens use these zones:

1. Header/identity area
2. Status/action bar
3. Summary cards
4. Primary workflow panel
5. Related records tabs
6. Audit/timeline panel
7. Safety/demo warnings if relevant

## 4. Patient Workspace

Patient Workspace is the primary patient object screen.

It includes:

- patient identity
- OIB/date/phone/email display
- clinical knowledge summary from reviewed Clinical Documents
- source links for every AI-assisted knowledge statement
- internal documents
- external documents
- procedures
- pathology
- laboratory
- imaging
- appointments
- invoices
- stock/material context through appointments where feasible
- audit timeline
- notes
- duplicate warning when available
- create appointment action

Appointments must use a resolved `patient_id`; no appointment may be made for an unknown patient.

The Patient Workspace now prioritizes knowledge before workflow. The first question is: what do we know about this patient, what remains unresolved, and where did each statement come from?

## 5. Appointment Workspace

Appointment Workspace includes:

- patient identity with link to Patient Workspace
- service/provider/room/time
- status flow
- material consumption
- invoice link or draft action
- stock movements
- audit timeline

Critical actions keep V19 `ActionButton` and `HelpHint` behavior.

## 5a. Episode Workspace

Episode Workspace gathers the clinical story around one patient context.

It includes:

- episode title/status/type/priority
- patient identity with link to Patient Workspace
- start/end dates
- owner provider
- summary and clinical notes
- active confirmed clinical plan
- pending AI suggestion when awaiting physician confirmation
- clinical decision timeline
- related appointments
- audit timeline
- close episode action
- create appointment for this episode action

Episode Workspace is not Workflow Engine, Knowledge Engine, autonomous AI automation or a new clinical module.

## 6. Invoice Workspace

Invoice Workspace should include:

- invoice identity/status
- patient/appointment links
- lines
- payment history
- fiscalization status
- audit timeline

The current invoice UI still uses the invoice list/detail panel pattern. A dedicated invoice detail route remains future work.

## 7. Inventory Item Workspace

Future Inventory Item Workspace standard:

- item identity
- current stock
- batches
- movements
- reorder status
- suppliers
- audit timeline

## 8. Purchase Order Workspace

Future Purchase Order Workspace standard:

- supplier
- status
- lines
- receiving workflow
- related stock movements
- audit timeline

## Current Implementation

- Shared workspace components live in `frontend/src/components/workspace/`.
- Patient Workspace exists at `/patients/:id`.
- Episode Workspace exists at `/episodes/:id`.
- Appointment detail follows the workspace pattern.
- Patient related appointments are loaded through `GET /api/patients/{patient_id}/appointments`.
- Patient related episodes are loaded through `GET /api/patients/{patient_id}/episodes`.
- Patient related invoices are loaded through `GET /api/patients/{patient_id}/invoices`.

## Relationship To Readiness Cockpit

`docs/V20_READINESS_COCKPIT.md` is a product/output document for the operational readiness view. It is not the Codex master prompt. The official V20 direction remains this workspace architecture sprint from `docs/CODEX_MASTER_PROMPT_V20.md`.
