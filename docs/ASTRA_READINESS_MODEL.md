# ASTRA Readiness Model

## 1. Purpose

Readiness is a read-only operational risk view before demo and pilot sessions.

It answers:

> What is blocking the next demo or pilot, and where do I go to inspect it?

Readiness connects the cockpit, workspaces, audit, inventory, billing and pilot evidence into one pre-demo entry point.

## 2. Readiness Is Not Compliance

Readiness is not:

- production certification
- GDPR approval
- real-data approval
- Croatian fiscalization approval
- medical-device certification

Real data readiness is governed by `docs/REAL_DATA_READINESS_CHECKLIST.md`.

## 3. Readiness Status Levels

- `ready_for_demo`: no critical blockers and no warnings.
- `attention_needed`: no critical blockers, but warnings must be reviewed or accepted for demo.
- `blocked`: at least one critical blocker exists; demo should not proceed unless the maintainer explicitly waives the risk.

## 4. Readiness Check Categories

- demo guardrails
- fiscalization mode
- clinic core data
- audit presence
- inventory risk
- invoice/payment risk
- API key risk
- pilot evidence risk

## 5. Link Readiness To Workspaces

Each readiness check should link to an operational screen when possible:

- patients -> `/patients`
- clinical documents awaiting review -> `/clinical-documents?review_status=needs_physician_review`
- stale patient clinical summaries -> `/patients`
- clinical episodes are experimental/deferred and should not block readiness
- providers -> `/appointments/new`
- rooms -> `/appointments/new`
- reception resource issues -> `/reception`
- services -> `/services`
- modules -> `/modules`
- audit -> `/audit-log`
- low stock -> `/inventory`
- expiring stock -> `/inventory`
- draft invoices -> `/invoices`
- unpaid invoices -> `/invoices`
- API keys -> `/api-keys`
- human pilot evidence -> `/readiness` for now; evidence remains documentation-governed

Future object workspaces should replace generic list targets when they exist.

Clinical documents awaiting review use the same Phase A semantics as Patient Clinical Knowledge helpers: `extracted` and `needs_physician_review` count as awaiting review; `draft`, `reviewed`, `rejected` and `superseded` do not.

Stale patient summaries are Operational Readiness warnings. They are not a Clinical Readiness Gate and do not certify clinical safety.

## 6. Readiness Target Contract

Every `target_path` returned by `/api/readiness` must point to an existing protected frontend route.

This is a product contract, not only a technical convenience:

- readiness identifies risk
- the target link opens the place where the risk can be inspected
- the workspace or list screen provides the next safe action
- audit and pilot evidence close the loop

If a readiness check has no real UI target yet, it should use `/readiness` and explain the documentation-governed next action in `action`.

The frontend pilot smoke test verifies that backend readiness target paths remain registered in `AppRoutes.tsx`.
