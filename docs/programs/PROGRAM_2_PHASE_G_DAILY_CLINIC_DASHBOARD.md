# Program 2 — Phase G: Daily Clinic Dashboard

## Status

Phase G implements the shared operational surface **Danas u poliklinici** and a backend-aggregated day endpoint.

## Backend projection

`GET /api/dashboard/day` returns one row per `PatientJourney` for the selected date. A single eager-loaded query retrieves patient, appointment, service, clinician, room and blockers, avoiding per-row database requests. Server-side filters cover clinician, room, service, workflow stage, blocker presence and patient search.

Each row exposes intake channel, documents, preparation, arrival, check-in, encounter, consumables, billing, payment and blocker status. `visible_sections` is derived from the caller's permissions so the same dashboard can serve reception, clinicians and billing without separate workflow dashboards.

## Frontend

The application home route renders `DailyClinicDashboard`. The operational table intentionally exposes only four columns: **Vrijeme i pacijent**, **Usluga i liječnik**, **Trenutačno stanje** and **Sljedeća radnja**. Documents, preparation, check-in, encounter, consumables and payment remain canonical sub-statuses, but the frontend projects them into one traffic-light signal and at most one contextual action.

The empty circle means not started, amber means active, red means a problem and green means completed. Text and a hover/focus explanation accompany every signal, so meaning never depends on color alone. Capabilities include selected date, clinician/room/service/stage/problem filters, patient search, manual refresh and permission-aware actions such as **Započni prijem**, **Otvori pregled**, **Evidentiraj materijal** and **Naplati**.

## Role and safety boundary

The dashboard may initiate only an already permission-protected administrative action: starting reception records arrival and opens the canonical check-in; entering billing may prepare the invoice after explicit confirmation. It never clears blockers, confirms preparation, resolves clinical items, records consumables or marks payment without a human action.

`allowed_actions` is calculated by the backend from RBAC permissions. Users without the relevant permission receive a neutral **Otvori** action instead of a mutation control.
