# V20 Readiness Cockpit

## Status

Implemented as a product/output document.

`docs/CODEX_MASTER_PROMPT_V20.md` is the official Codex master prompt for V20 and defines the Workspace Architecture and Clinical Navigation Sprint. This readiness cockpit is an additional operational output that complements the workspace direction.

## Purpose

V20 adds a single readiness cockpit for demo and pilot operations. It is intentionally informational: it does not create, update or delete clinic data.

The cockpit answers one practical question before a walkthrough:

> Is ASTRA safe and understandable enough for the next demo/pilot pass?

## Scope

- `GET /api/readiness`
- Frontend route `/readiness`
- Navigation item `Spremnost`
- Smoke and backend test coverage

## Checks Included

- Demo guardrail and real-data flag
- Fiscalization mode
- Basic Clinic Core setup: patients, providers, rooms, services, modules
- Audit log presence
- Inventory low-stock and expiring batch warnings
- Draft and unpaid invoices
- Active API keys

## Architecture Bible Check

- Human above software: users can see operational risk before acting.
- One source of truth: readiness is calculated by the backend API.
- One language: the UI uses existing Clinic Core terms.
- Modular Clinic Core: no new medical module or EMR scope is introduced.
- API First: the same readiness state is available to UI, external systems and AI agents.
- Audit and safety: the endpoint is read-only and requires an authenticated user with audit-read permission.

## Limitations

This is not a production compliance certification. It is a pilot readiness view. Real-data approval still depends on `docs/REAL_DATA_READINESS_CHECKLIST.md`.
