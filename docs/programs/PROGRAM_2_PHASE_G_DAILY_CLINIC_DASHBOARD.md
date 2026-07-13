# Program 2 — Phase G: Daily Clinic Dashboard

## Status

Phase G implements the shared operational surface **Danas u poliklinici** and a backend-aggregated day endpoint.

## Backend projection

`GET /api/dashboard/day` returns one row per `PatientJourney` for the selected date. A single eager-loaded query retrieves patient, appointment, service, clinician, room and blockers, avoiding per-row database requests. Server-side filters cover clinician, room, service, workflow stage, blocker presence and patient search.

Each row exposes intake channel, documents, preparation, arrival, check-in, encounter, consumables, billing, payment and blocker status. `visible_sections` is derived from the caller's permissions so the same dashboard can serve reception, clinicians and billing without separate workflow dashboards.

## Frontend

The application home route now renders `DailyClinicDashboard`. The page uses the existing ASTRA design system and Croatian copy. Its status rail is the primary visual device: every workflow dimension has an icon and textual state, so meaning never depends on color alone.

Capabilities include selected date, clinician/room/service/stage/blocker filters, patient search, manual refresh, last-refresh time, row count, arrival count, blocker count and navigation to the appointment context. The table remains horizontally scrollable on smaller screens and controls have visible keyboard focus through the shared design system.

## Role and safety boundary

The dashboard is an operational read projection. It does not change workflow state, clear a blocker, approve preparation or make clinical decisions. Existing permission-protected detail surfaces own all mutations.

## Deferred to later phases

- Phase H structured check-in mutation surface
- Phase I full patient journey/encounter workspace route
- role-specific column hiding based on a frontend current-user capability endpoint
