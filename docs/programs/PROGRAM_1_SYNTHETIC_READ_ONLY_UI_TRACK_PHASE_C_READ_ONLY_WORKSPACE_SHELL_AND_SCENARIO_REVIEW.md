# Program 1 Synthetic Read-Only UI Track Phase C - Read-Only Workspace Shell and Scenario Review

Status: complete.

Route: `/program1/synthetic-review`.

Navigation: `Program 1 Demo`, visible through the existing application shell when demo/development safety banner conditions are active.

Page composition:

- persistent synthetic safety banner
- local synthetic search/filter section
- scenario selector
- scenario overview
- tabbed review sections
- neutral two-scenario comparison

Interactions:

- select scenario
- switch tabs
- filter synthetic content in memory
- select two scenarios for comparison
- reset comparison view

No-action boundary:

- no create, edit, save, submit, approve, reject, override, assign, escalate, send, message, schedule, cancel, complete, sign, writeback, export, download, print, upload, import, connect, or synchronize action is present.

Safety banner:

- states `SINTETICKI PODACI`
- states `NIJE ZA KLINICKU UPORABU`
- states `NE SADRZI PODATKE STVARNIH PACIJENATA`
- states no diagnosis, therapy, triage, real patient data entry, persistence, export, or clinical writeback

Screenshots are not created as evidence in this phase. Browser validation remains manual/local only.

Test coverage:

- frontend smoke checks assert route, navigation, safety banner, fixtures, validation, and absence of prohibited storage/network/export primitives in the new module.
