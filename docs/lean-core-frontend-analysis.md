# Lean Core frontend request and bundle analysis

## Scope and method

This analysis covers Increment D of Module 3.5. Request counts were taken from
the production frontend call graph and verified by focused component tests. The
bundle comparison uses the emitted Vite production build and `dist/index.html`,
not development-mode request counts (React StrictMode intentionally repeats
effects in development).

## Request map

Every authenticated screen also uses the application shell requests for public
configuration and available clinics. Authentication initialization performs one
session request. The counts below describe screen-owned requests unless noted.

| Screen | Mount requests | Context/filter changes | Detail or mutation behavior |
| --- | --- | --- | --- |
| Daily dashboard | dashboard, rooms, services; providers only when clinician filtering is permitted | date, clinic, status and search replace the dashboard request; the previous request is aborted | reception detail loads only when its modal opens; a completed mutation refreshes the dashboard |
| Patient directory | patient list | directory query refreshes the list | patient detail is a lazy route |
| Patient detail | identity, documents, summary, findings, timeline, appointments, invoices, laboratory, therapies and audit | duplicate search is conditional | unchanged in this increment; splitting its existing sections needs a separate UX decision |
| Institution clinical documents | metadata list; patient lookup only after two search characters | metadata filters replace the list request | document content is loaded by the lazy detail route |
| Clinical document detail / signed report | document, audit, evidence timeline and addenda | none | source/detail data belongs to the explicitly opened record; mutations refresh relevant projections |
| Appointment booking | services, clinics, providers and rooms; patient/episode requests are conditional | patient search and patient selection replace their respective request | create is one mutation, then navigation |
| Package booking | packages, services, providers and rooms; patient search is conditional | preview is explicit | booking is one mutation |
| Billing list | invoice list | none | invoice issue/payment/line mutations refresh only the selected invoice |

`useApi` now aborts superseded requests and ignores aborted resolutions. A null
path explicitly means “not needed yet” and performs no request. This prevents a
late clinic/date/patient response from overwriting the active view.

## Patient journey workspace

Before this increment the workspace mounted 15 endpoint hooks immediately and
then issued a sixteenth clinical-document request after the journey supplied the
real patient ID. One of those requests used `patient_id=0`.

After this increment:

- the documents/preparation entry path performs 9 requests;
- an explicit encounter entry path performs 8 requests;
- check-in, preparation, encounter, closure, inventory, public configuration,
  visit-document and pathology projections load only for the visible stage;
- provider lookup is skipped when the journey already embeds its provider;
- clinical documents wait for the real patient ID;
- direct `focus=encounter` initialization avoids first loading the documents
  stage and then the encounter stage.

Timeline, AI-summary metadata, services and clinical-document metadata remain
available because the workspace exposes that clinical context from every stage.
Deferring those would add clicks or change current behavior, so it was not done.

## Dashboard

The dashboard continues to request only its daily projection and small filter
catalogs. It does not request a patient clinical record, signed reports or full
billing details. Provider lookup is now omitted for roles that cannot filter by
clinician. Rooms and services remain eagerly available because hiding their
filter values until a second interaction produced no material payload evidence
and would complicate the existing filter control.

The existing dashboard calculations already use memoized primitive projections
for blocks, lanes, range, summary and room groups. Focused render tests showed no
functional reason to add component-wide `memo`, `useCallback` or list
virtualization. A clinic day contains tens to hundreds of projected rows, and the
backend owns filtering, so pagination/virtualization was not added blindly.

## Production bundle comparison

| Artifact | Before | After |
| --- | ---: | ---: |
| entry JavaScript | 239,861 B | 63,851 B |
| React vendor | 232,866 B | 232,866 B |
| icon vendor | 26,278 B | 26,273 B |
| patient journey route | 96,980 B and initially preloaded | 73,686 B, loaded on route entry |
| Program 1 | 34,995 B and initially preloaded | 35,252 B, loaded on route entry |
| operations pages | 14,369 B and initially preloaded | separate lazy route chunks |

The previous static route imports and broad manual chunks caused Vite to emit
module-preload links for rare routes. The final `index.html` preloads only React
and icons. Clinical workspace, administration, audit, documents, billing,
inventory and Program 1 are dynamic route chunks.

The final build produced more small route chunks. This is intentional at the
route boundary: they are not fetched on login/dashboard, while shared React and
icons remain stable vendor chunks. No runtime dependency or state-management
framework was added.

## Validation

- TypeScript typecheck
- focused `useApi`, dashboard and patient-journey tests
- full frontend contract and Vitest suite
- Vite production build and emitted preload inspection
- frontend smoke test
