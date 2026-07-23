# Focused patient journey workspace

## Goal

The patient journey workspace keeps the current operational stage in focus.
Clinical context remains available without competing with reception, encounter,
consumables or billing work.

This phase changes presentation and request timing only. It does not change
workflow transitions, RBAC, institution scope, clinical-document provenance,
signed-report immutability, CSRF, audit or human clinical ownership.

## Progressive disclosure

`Klinički kontekst` is collapsed by default. Opening it loads the summary tab.
The timeline and source-document list are loaded only after their own tab is
selected.

The same rule applies to stage refresh:

- billing data refreshes only in the billing stage;
- visit documents and pathology follow-up refresh only in the documents stage;
- hidden stages do not create background request fan-out.

The service catalogue remains available because it labels every activity in a
multi-activity physical visit.

## Safety boundaries

- Source documents remain the source of truth.
- AI summary remains a derived, source-linked layer requiring human review.
- Hiding a panel never grants or removes a backend permission.
- No workflow transition, clinical gate or billing gate is bypassed.
- Unsaved clinical-form navigation protection remains active.
- Audit and institution/clinic scope remain backend-enforced.

## Regression evidence

Frontend tests verify that:

- only the active operational stage is rendered;
- direct encounter entry does not load hidden stages;
- summary, timeline and documents are absent from initial requests;
- each clinical-context data source is loaded only when opened;
- switching activities cannot silently discard an unsaved clinical draft.
