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
- providers -> `/appointments/new`
- rooms -> `/appointments/new`
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
