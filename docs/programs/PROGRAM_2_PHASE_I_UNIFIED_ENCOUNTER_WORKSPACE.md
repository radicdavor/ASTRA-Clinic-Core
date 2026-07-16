# Program 2 — Phase I: Unified Encounter Workspace

> Historical phase record. It is not the current product-state source; see the canonical documents in `docs/`.

## Canonical contract

`JourneyEncounter` is a one-to-one clinical note for `PatientJourney`. It links the existing clinical episode when present and never duplicates patient, appointment, source document, inventory or invoice data.

The encounter may open only from `READY_FOR_CLINICIAN`, after check-in is ready and blockers are resolved. Opening, editing and completion require dedicated permissions and are audited. Completion requires human-entered clinical content, marks the encounter completed and uses the Phase B transition service to reach `PROCEDURE_COMPLETED`.

The workspace route `/journeys/{id}` presents identity and readiness in the header, source-linked timeline/documents and reviewed AI proposals on the left, the current human-authored encounter note in the center, and check-in/blockers/consumables/billing/payment state on the right. AI text is never inserted into the formal note automatically.

## Clinical boundary

Diagnosis, treatment, recommendation, procedural completion and use of any proposed fact remain explicit clinician actions. Completed encounter notes cannot be silently edited.
