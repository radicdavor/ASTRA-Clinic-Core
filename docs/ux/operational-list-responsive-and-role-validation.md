# Operational lists: responsive, role and clinic-time validation

Status: Phase F

Date: 23. 07. 2026.

## Before / after

Before this track, operational and technical fields competed for the same
horizontal space. At 1024 px the document list used eight columns, invoice
details were mixed into the list workflow and audit details had no consistent
progressive disclosure pattern.

After the track:

- documents use six primary columns and keep provenance on the detail route;
- invoices use six operational columns and load lines and payments only when
  the drawer is opened;
- audit uses six PHI-safe columns and loads technical metadata into an
  accessible read-only drawer;
- all three screens retain a textual status, one primary action and keyboard
  access to secondary actions;
- at 1024 px the available application content width accommodates the
  720-pixel table contract without creating horizontal scroll on the whole
  page; less important values are rendered as secondary text.

## Role boundaries

- Document permission failures render a distinct `Nemate dozvolu` state.
- Invoice action capabilities come from the active-clinic-scoped backend
  projection. UI visibility is not treated as authorization.
- Audit remains protected by `audit.read` and returns only the PHI-safe
  projection. Global security audit is not exposed through this clinic list.
- Reception, physician, billing and administrator navigation remains governed
  by the existing shell and backend permissions; this phase does not widen any
  scope.

## Accessibility

- Lists have accessible table names and one `h1`.
- Filter groups are labelled regions.
- Operational status contains text and is not represented by colour alone.
- The more menu is keyboard reachable.
- Progressive drawers trap focus, close with Escape and return focus to the
  opening control.
- Loading and error content uses the existing announced status/error patterns.

## Clinic-local day regression

`getClinicToday` is covered for Europe/Zagreb standard time, daylight-saving
time and the local-midnight boundary where UTC and clinic dates differ.
Changing the stored active-clinic timezone changes the derived day for the same
instant. The daily dashboard now calculates its initial day when the component
mounts, rather than once when the JavaScript module is imported.

## Validation

Focused Phase F run:

- Program 2 contract tests: 4 passed.
- Frontend focused tests: 32 passed.
- Docker Compose rebuild and production frontend build: passed.

The full frontend, DB-backed browser and backend security gates are Phase G
closure evidence and must not be inferred from these focused results.
