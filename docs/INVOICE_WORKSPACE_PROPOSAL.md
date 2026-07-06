# Invoice Workspace Proposal

## Purpose

Invoices should eventually become object-centered workspaces, matching the Patient and Appointment Workspace direction.

## Current Limitation

The current invoice UI uses a list/detail panel pattern inside `/invoices`. This is acceptable for the pilot, but it is less direct than a dedicated object screen.

## Proposed Route

`/invoices/:id`

## Required Elements

- invoice header/status
- patient link
- appointment link
- invoice lines
- payment history
- fiscalization status
- audit timeline

## Migration Plan

1. Keep `/invoices` as the searchable operational list.
2. Add `/invoices/:id` as the object-centered invoice workspace.
3. Move the existing selected-invoice panel into reusable workspace sections.
4. Preserve issue/payment `ActionButton` confirmations.
5. Preserve demo/noop fiscalization warnings.
6. Add invoice audit timeline.
7. Update readiness invoice checks to link directly to invoice filters or detail routes when available.

## Readiness Link Direction

Invoice readiness checks currently open `/invoices` because the dedicated Invoice Workspace is deferred.

Eventually:

- draft invoice checks should open `/invoices/:id` or a filtered invoice workspace
- unpaid invoice checks should open the relevant invoice workspace
- invoice issue/payment audit should appear in the Invoice Workspace audit panel

This is deferred until the readiness-workspace loop is stable. The current list/detail panel remains acceptable for pilot.

## Non-Goals

- No real fiscalization.
- No accounting integration.
- No production billing certification.
