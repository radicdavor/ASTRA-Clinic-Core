# Lean Core polling and background-work inventory

## Result

ASTRA Clinic Core has no application-runtime polling loop, busy loop, scheduler,
queue worker, WebSocket refresh process, Redis dependency or Celery process.
The daily dashboard refreshes on context changes, explicit user refresh and
successful reception mutations. This already matches the lean-core target, so
Increment E adds no polling mechanism and removes no justified one-shot timer.

## Frontend timers

| Location | Timing | Purpose | Hidden-tab cost | Decision |
| --- | ---: | --- | --- | --- |
| `ToastHost` | one shot, 5.2 s | dismiss the currently visible toast | one pending timer only while a toast is visible; cleanup cancels it | keep |
| `ReceptionFloatingModal` | one shot, 0 ms | move focus to an optimistic-concurrency conflict | one event-loop turn after an explicit conflict | keep |
| `VisitDocumentCenter` | one shot, 0 ms | allow print preview state to render before `window.print()` | only after an explicit print action | keep |
| `DailyClinicDashboard` | one shot, 0 ms | restore keyboard focus after closing reception | only after an explicit modal close | keep |

There is no `setInterval`, refetch interval or automatic dashboard refresh in
`frontend/src`. None of the one-shot timers performs network I/O or repeats.

## Backend work

- FastAPI starts one API process and does not create an application background
  task, scheduler or maintenance loop.
- Session validity is enforced by the authenticated request path. The frontend
  fetches the session once during application initialization and clears session
  state after an HTTP 401; it does not poll the session endpoint.
- `cleanup_expired_sessions` is a callable maintenance service only. It is not
  invoked on every request or from a resident loop.
- Schema readiness is checked by `/ready`. Production may perform one configured
  startup readiness check, but there is no repeated scan.
- Reminder rows and communication events do not imply a resident dispatcher in
  the current runtime. Delivery remains an explicit/stubbed workflow boundary.

## Test-only waits

`frontend/scripts/run-db-backed-e2e.mjs` uses a bounded 500 ms readiness retry
and a one-second process-start wait. These execute only in the DB-backed E2E
orchestrator, have a deadline and terminate with the test process. Playwright's
`expect.poll` calls verify browser storage cleanup in tests only. They are not
part of the product bundle or production process model.

## Operational rules

- Refresh after a successful mutation and on clinic/date/filter context change.
- Keep manual refresh on the daily dashboard.
- Do not introduce periodic dashboard polling unless a measured operational
  need appears; if introduced later, use 30–60 seconds, pause in hidden tabs and
  never overlap requests.
- Do not introduce periodic session validation.
- Run session cleanup through a bounded CLI/scheduled invocation, not inside the
  API process.
- Do not create a permanent reminder, audit or backup worker without a measured
  need and an explicit architecture decision.

## Verification

The inventory was produced with scoped searches over `frontend/src` and
`backend/app` for intervals, timeouts, polling, background tasks, task creation,
sleep loops, schedulers, workers, Redis and Celery. Generated bundles,
dependencies, tests and historical program documents were excluded from the
runtime conclusion.
