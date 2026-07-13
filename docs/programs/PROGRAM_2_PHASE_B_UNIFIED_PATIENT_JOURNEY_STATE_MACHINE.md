# Program 2 Phase B — Unified Patient Journey State Machine

## Workflow stages

`requested`, `booked`, `awaiting_forms`, `awaiting_documents`, `preparation_in_progress`, `ready_for_arrival`, `arrived`, `check_in_review`, `ready_for_clinician`, `in_encounter`, `procedure_completed`, `awaiting_billing`, `awaiting_payment`, `completed`, `cancelled`, `no_show`, `blocked`.

Stages describe progress. Blockers and sub-statuses describe why progress may not continue.

## Sub-status vocabularies

- Documents: `not_requested`, `requested`, `partial`, `complete`, `review_required`, `blocked`.
- Preparation: `not_assigned`, `assigned`, `acknowledged`, `in_progress`, `complete`, `review_required`, `blocked`.
- Check-in: `not_arrived`, `arrived`, `in_review`, `ready`, `blocked`.
- Encounter: `not_started`, `in_progress`, `completed`, `aborted`.
- Consumables: `not_ready`, `pending`, `confirmed`, `not_applicable`.
- Billing: `not_ready`, `ready`, `invoice_created`, `adjustment_required`, `closed`.
- Payment: `not_due`, `unpaid`, `partially_paid`, `paid`, `refunded`, `cancelled`, `deferred`.

## Guard rules

- A transition not listed in the service transition graph returns conflict and changes nothing.
- `ready_for_clinician` and `in_encounter` require check-in `ready` and no open blocker.
- `procedure_completed` requires encounter `completed`.
- `awaiting_payment` requires billing `invoice_created`.
- `completed` requires encounter complete, consumables confirmed/not applicable, billing closed and payment resolved (`paid`, `refunded`, `cancelled` or explicitly `deferred`).
- Clinical blockers are never cleared automatically.
- Terminal stages are immutable.
- `blocked` is a visible stage; the separate blocker records retain category, clinical ownership and resolution evidence.

## API contract

- `POST /api/patient-journeys`
- `GET /api/patient-journeys`
- `GET /api/patient-journeys/{id}`
- `POST /api/patient-journeys/{id}/transition`
- `PATCH /api/patient-journeys/{id}/statuses`
- `POST /api/patient-journeys/{id}/blockers`
- `POST /api/patient-journeys/{id}/blockers/{blocker_id}/resolve`

All mutations require dedicated journey permissions and produce audit evidence.
