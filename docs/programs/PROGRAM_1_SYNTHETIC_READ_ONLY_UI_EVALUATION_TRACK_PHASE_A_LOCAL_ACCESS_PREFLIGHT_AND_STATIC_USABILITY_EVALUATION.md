# Program 1 Synthetic Read-Only UI Evaluation Track Phase A

## Local Access Preflight and Static Usability Evaluation

Status: complete.

## Scope

Phase A evaluates the existing `/program1/synthetic-review` route without adding or changing runtime functionality.

Authorized boundary:

- local-only
- repository-controlled synthetic fixtures only
- read-only evaluation
- existing UI only
- static, build, smoke, and browser access-preflight checks

Not authorized:

- real data, PHI, or PII
- backend Program 1 integration
- authentication bypass or authentication redesign
- persistence, export, upload, or download
- clinical workflow, diagnosis, treatment, triage, or patient messaging
- production deployment, clinical use, or go-live

## Browser Access Preflight

The local frontend returned HTTP 200 for `/program1/synthetic-review`.

A real browser navigation rendered the application and redirected the route to `/login` through the existing protected application shell. After the local Docker database and backend were started, the repository-controlled demo credentials established a valid local session and the authenticated Program 1 workspace rendered at `/program1/synthetic-review`.

Port `5173` was already occupied by an unrelated local NURA development process. The evaluation therefore used the existing ASTRA Vite server on port `4174` and the ASTRA backend on port `8000`. The unrelated process was not stopped or changed.

Decision:

- browser rendering infrastructure: `PASS`
- route-level HTTP serving: `PASS`
- authenticated Program 1 workspace rendering: `PASS`
- desktop DOM and interaction evaluation: `PASS`
- narrow-viewport layout evaluation: `PASS AFTER RESPONSIVE FIX`
- browser console errors on the Program 1 route: `NONE OBSERVED`

## Completed Verification

- `npm run typecheck`: pass
- `npm run smoke`: pass
- `npm run build`: pass
- `python -m unittest discover tests/sandbox/program1`: 53 tests passed
- static Program 1 UI search for network, storage, export, file, and streaming primitives: no matches
- responsive rules reviewed for single-column collapse below 980 px
- authenticated browser render confirmed with all five synthetic scenarios
- filter no-match empty state confirmed
- scenario selection confirmed with `SYN-GAMMA`
- findings tab activation and content confirmed
- 390 px viewport confirmed without page-level horizontal overflow after responsive correction
- comparison table remains intentionally scrollable inside its bounded container at narrow width
- controls reviewed as native inputs, selects, buttons, and tab controls
- safety banner, limitations, prohibited interpretations, empty-state handling, and synthetic labeling remain present in source

The frontend build emitted pre-existing non-blocking warnings about Tailwind content configuration and React Router module directives. No Program 1 build failure occurred.

## Static Usability Findings

Confirmed strengths:

- persistent synthetic-demo labeling
- explicit local/in-memory search explanation
- scenario overview, timeline, evidence, findings, completeness, limitations, and comparison are separated into understandable sections
- native filter controls and semantic section headings are used
- mobile-width CSS collapses scenario, card, two-column, and comparison layouts to one column
- no action, writeback, export, upload, diagnosis, treatment, triage, or patient-messaging control exists in the Program 1 module

Responsive correction completed during evaluation:

- Program 1 grid children now allow shrinking inside the mobile shell
- Program 1 page headers stack vertically below 980 px
- Program 1 labeled inputs and selects fit the available width
- page-level horizontal overflow at 390 px was reduced from 778 px document width to the 375 px client width
- smoke guards preserve the responsive rules

Remaining limitations:

- screenshot capture in the browser inspection tool timed out, so verification used rendered DOM, computed layout metrics, interaction state, and console logs
- formal keyboard traversal and contrast certification were not performed
- no clinician usability or clinical validation claim is made

## Phase A Decision

`GO` for completion of local synthetic-only browser/usability evaluation within the read-only boundary.

`NO-GO` for runtime expansion, real data, backend Program 1 integration, persistence, export, clinical workflow, production use, clinical use, or go-live.

## Restored Hold

Phase A is closed with the following hold:

- no authentication changes authorized
- no Program 1 functional runtime expansion authorized
- no further evaluation phase started
- no real-data or clinical-use authorization
- default posture: `STOP AND HOLD`
