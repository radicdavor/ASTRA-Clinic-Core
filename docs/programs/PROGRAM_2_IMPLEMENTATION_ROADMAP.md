# Program 2 — Implementation Roadmap

## Mission

One canonical workflow: `Prijava → dokumenti → priprema → dolazak → provjera → pregled → potrošni materijal → račun → plaćanje → završetak`.

## Architecture inventory

| Capability | Existing source of truth | Program 2 decision |
|---|---|---|
| Identity | `Patient` | Reuse; never duplicate identity |
| Scheduling/intake source | `Appointment` | Reuse; journey is one-to-one with appointment |
| Clinical continuity | `ClinicalEpisode` | Link through appointment |
| Documents/source evidence | `ClinicalDocument` and reviewed summaries | Reuse and later add journey linkage additively |
| Readiness | readiness previews, snapshots and acknowledgments | Reuse as advisory evidence; never automatic clearance |
| Tasks/checklists | workflow templates/tasks/items | Reuse for operational assignments; journey statuses remain canonical aggregate state |
| Consumables | `StockMovement` linked to appointment | Reuse ledger; do not create parallel stock records |
| Billing/payment | `Invoice`, `InvoiceLine`, `PaymentTransaction` | Reuse; project their state into journey |
| Audit | `AuditLog` | Reuse plus journey-local event timeline |
| Therapy/laboratory | structured module records | Link through patient/episode/appointment where present |

## Phases

- [x] A — domain contract and additive foundation
- [x] B — explicit state machine, blockers and transition audit
- [x] C — shared intake orchestration and safe channel boundaries
- [x] D — versioned preparation/forms/reminder contracts
- [ ] E — document ingestion and OCR provider boundary
- [ ] F — unified timeline and source-linked summary projection
- [ ] G — daily clinic dashboard
- [ ] H — reception check-in
- [ ] I — encounter workspace
- [ ] J — consumables, billing, payment and closure orchestration
- [ ] K — full validation and formal closure

No later phase may bypass the Phase B transition service.
