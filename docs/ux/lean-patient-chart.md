# Lean patient chart

## Goal

The patient chart should answer three questions without making the user scan a long dashboard:

1. Is this the correct patient?
2. What requires attention now?
3. Where is the detailed record when it is needed?

This phase changes presentation and loading behavior only. It does not change clinical-document provenance, role permissions, audit rules, signed-record immutability or the human-review boundary.

## Before

The patient page rendered:

- three equally prominent create actions;
- a six-cell summary strip and a second six-cell metrics grid;
- a full identity section;
- clinical tasks, derived-data notice, summary, findings and evidence timeline at once;
- a sticky knowledge sidebar repeating counts and exceptions;
- eleven detailed tabs;
- eleven eager API reads on initial display.

This made counts compete with current work and made source-linked clinical information visually indistinguishable from ordinary operational data.

## After

The page has one primary action, `Novi termin`, and two secondary actions in a controlled menu.

Five top-level sections provide progressive disclosure:

1. `Pregled`
2. `Dokumenti`
3. `Laboratorij i terapije`
4. `Termini i računi`
5. `Izvori i evidencija`

The overview contains:

- compact patient identity;
- the next appointment;
- only exceptions that currently require attention;
- operational tasks;
- the clearly labelled derived-data notice;
- the source-linked patient summary.

Normal counts and duplicated metric cards are removed. Detailed clinical findings, evidence timeline and audit are available only in `Izvori i evidencija`.

## Loading contract

The initial overview loads only:

- patient;
- possible duplicate candidates;
- appointments;
- clinical documents needed for review exceptions and summary sources;
- clinical summary;
- workflow tasks.

The following reads are deferred until their section opens:

- laboratory orders and therapies;
- invoices;
- clinical findings;
- clinical evidence timeline;
- audit log.

This reduces initial request fan-out without changing any backend endpoint or authorization rule.

## Safety boundaries

- Source documents remain the source of truth.
- AI content remains labelled as a draft or reviewed summary.
- AI actions remain explicit and require human review.
- Clinical findings and timeline remain read-only source-linked views.
- Audit remains visible to authorized users in its dedicated section.
- No backend permission, institution scope, clinic scope or mutation rule is changed.

## Responsive and accessibility behavior

- Tabs use the ARIA tab pattern and support arrow, Home and End keys.
- The active tab can be controlled by the patient page so deferred loading follows the visible section.
- The tab list scrolls horizontally on narrow screens.
- Identity fields collapse from four columns to two and then one.
- The secondary-action menu remains reachable on mobile without widening the page.

## Regression evidence

Frontend tests cover:

- five-section information architecture;
- one primary action;
- deferred API loading;
- preservation of document type, source and physician-review status;
- keyboard navigation and focus behavior.
