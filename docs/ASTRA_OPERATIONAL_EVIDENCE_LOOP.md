# ASTRA Operational Evidence Loop

## Purpose

ASTRA must connect operational risk, safe action and release evidence into one understandable loop.

The loop is:

`Readiness -> Workspace -> Action -> Audit -> Pilot/Release evidence`

## 1. Readiness Identifies Operational Risk

The Readiness Cockpit shows demo guardrails, fiscalization mode, clinic core data, audit presence, inventory risk, invoice/payment risk, API key risk and pilot evidence risk.

Each readiness check should show:

- status
- decision impact
- reason
- next action
- target screen when available

## 2. User Follows Target Link To Workspace

A readiness check should guide the user to the most useful screen:

- low stock -> Inventory
- draft invoice -> Invoices
- unpaid invoice -> Invoices
- missing audit context -> Audit log
- patient issue -> Patient Workspace
- appointments without episode -> Episodes

## 3. User Performs Guided Action

Actions use the V19 pattern:

- `ActionButton`
- `HelpHint`
- confirmation when critical
- clear success/error feedback

The user remains responsible. ASTRA organizes and documents.

## 4. Backend Writes Audit

Important create/update/delete and workflow actions must create audit evidence.

Audit should remain raw enough for reconstruction and readable enough for pilot users to understand what happened.

## 5. Readiness Improves Or Remains Warning

After action, the user can return to `/readiness` and verify whether the risk changed.

Warnings may remain acceptable for demo if explicitly reviewed.

Critical blockers require maintainer waiver before demo.

## 6. Pilot/Release Evidence Is Updated

Readiness does not replace human evidence. Pilot/release docs record:

- what was checked
- what remained warning
- whether anything was waived
- Go/No-Go decision

## Examples

### Low Stock

Low stock -> Inventory -> purchase receive -> stock movement/audit -> readiness review.

### Draft Invoice

Draft invoice -> invoice UI -> issue/payment -> audit -> readiness review.

### Clinical Episodes

Appointments without episode -> Episodes -> create/link episode -> episode/appointment audit -> readiness review.

### Missing Human Pilot Evidence

Human pilot evidence warning -> pilot docs -> ADR/Go-No-Go update -> release decision.
