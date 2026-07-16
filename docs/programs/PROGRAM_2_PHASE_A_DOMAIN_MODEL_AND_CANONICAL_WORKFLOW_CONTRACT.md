# Program 2 Phase A — Domain Model and Canonical Workflow Contract

> Historical phase record. It is not the current product-state source; see the canonical documents in `docs/`.

## Decision

`PatientJourney` is the single operational aggregate for one visit and has a one-to-one relationship with `Appointment`. It coordinates existing sources of truth; it does not replace them.

## Entity and relationship map

```text
Patient 1 ── * Appointment 1 ── 1 PatientJourney
                  │                     ├── * JourneyEvent
                  │                     └── * JourneyBlocker
                  ├── Service / Provider / Room / Clinic
                  ├── ClinicalEpisode ── documents / plans / therapies
                  ├── ClinicalDocument / readiness evidence
                  ├── StockMovement
                  └── Invoice ── PaymentTransaction
```

Service, clinician, room, clinic and planned time are derived from the linked appointment and are exposed by the journey API. They are not copied into journey columns.

## Aggregate fields

Stable ID, patient and appointment IDs, intake channel, current stage, document/preparation/check-in/encounter/consumables/billing/payment statuses, created/updated actor metadata and closed timestamp.

## Source-of-truth and ownership rules

- `Patient`: identity and contact data.
- `Appointment`: scheduling, service, clinician, room, time and original scheduling source.
- `PatientJourney`: cross-module workflow stage and projections only.
- `ClinicalDocument`: original/derived clinical document layers and review state.
- `ClinicalEpisode`: longitudinal clinical context.
- inventory ledger: confirmed material movement.
- invoice/payment records: financial truth.
- `JourneyEvent`: immutable operational journey timeline.
- `AuditLog`: security/audit reconstruction.

## Mutation rules

- Journey creation is idempotency-protected by a unique appointment ID.
- Intake channel is exactly `web`, `ai_secretary` or `manual`.
- Stage changes only use the transition service.
- Sub-status changes use the status service and validated vocabularies.
- Clinical blockers require explicit human resolution; software never clears them automatically.
- Terminal journeys cannot be edited.

## Audit rules

Creation, transition, sub-status change, blocker creation and blocker resolution create both a standard audit record and a journey event containing actor, request ID, source channel and transition context.

## Prohibited duplicate models

No Program 2 patient, appointment, episode, document, inventory movement, invoice, payment or AI clinical fact table may duplicate an existing source of truth. Future phase tables may only represent preparation/form/request/communication/encounter concepts that do not already exist.

## Migration impact

Migration `0039_program2_journey` is additive. It creates three new tables and indexes, changes no existing column, and can be downgraded by dropping only Program 2 foundation tables.
