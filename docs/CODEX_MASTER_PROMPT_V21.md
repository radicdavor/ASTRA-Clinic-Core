# Codex master prompt v21 — Readiness and Workspace Convergence Sprint

Use this prompt in Codex after V20 has been implemented.

---

You are a senior full-stack architect, healthcare workflow designer, and release-readiness maintainer.

Before making changes, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md`
- `docs/ASTRA_DESIGN_SYSTEM.md`
- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `docs/V20_READINESS_COCKPIT.md`
- `docs/CODEX_MASTER_PROMPT_V20.md`

## Current state after V20

V20 appears to have implemented two important directions:

1. **Workspace Architecture**
   - Patient Workspace exists at `/patients/:id`.
   - Appointment detail follows the workspace pattern.
   - Workspace docs exist.
   - Patient-related appointments and invoices are available through patient-id endpoints.

2. **Readiness Cockpit**
   - `/api/readiness` exists.
   - `/readiness` frontend route exists.
   - `docs/V20_READINESS_COCKPIT.md` exists.
   - Readiness cockpit is read-only and supports demo/pilot safety checks.

This is good. But it creates a new responsibility: readiness, workspace navigation, and pilot release evidence must not become separate worlds.

## Sprint name

**Readiness and Workspace Convergence Sprint**

## Main goal

Make the Readiness Cockpit, Patient Workspace, Appointment Workspace, and pilot evidence flow work together as one operational system.

The user should be able to answer:

> What is blocking the next demo/pilot, and where do I go to fix or inspect it?

## Non-negotiable rules

- Do not enable real patient data.
- Do not implement real Croatian fiscalization.
- Do not add broad new clinical modules.
- Do not add AI receptionist or external integrations.
- Do not change Architecture Bible directly without maintainer request.
- Keep demo warnings visible.
- Keep noop/stub fiscalization warnings visible.
- Keep readiness endpoint read-only.
- Keep workspace actions consistent with ActionButton/HelpHint rules.

---

# Phase 1 — Document readiness-workspace relationship

Create:

`docs/ASTRA_READINESS_MODEL.md`

Required sections:

## 1. Purpose

Define Readiness as a read-only operational risk view before demo/pilot sessions.

## 2. Readiness is not compliance

State clearly:

- readiness is not production certification
- readiness is not GDPR approval
- readiness is not fiscalization approval
- real data readiness is governed by `docs/REAL_DATA_READINESS_CHECKLIST.md`

## 3. Readiness status levels

Define:

- `ready_for_demo`
- `attention_needed`
- `blocked`

Define what each means.

## 4. Readiness check categories

Define categories:

- demo guardrails
- fiscalization mode
- clinic core data
- audit presence
- inventory risk
- invoice/payment risk
- API key risk
- pilot evidence risk

## 5. Link readiness to workspaces

Each readiness check should ideally have a navigation target:

- patients -> Patient list/workspace
- providers -> provider setup if available
- rooms -> room setup if available
- services -> Services
- modules -> Modules
- audit -> Audit log
- low stock -> Inventory
- expiring stock -> Inventory
- draft invoices -> Invoices
- unpaid invoices -> Invoices
- API keys -> API Keys
- human pilot evidence -> pilot docs, no UI route yet

Acceptance criteria:

- `docs/ASTRA_READINESS_MODEL.md` exists.
- It is linked from `docs/V20_READINESS_COCKPIT.md` and README.

---

# Phase 2 — Add navigation targets to readiness checks

Backend:

Extend `ReadinessCheck` schema with optional fields:

- `target_path: str | None`
- `target_label: str | None`

Update `/api/readiness` checks to include target paths where useful:

- patients -> `/patients`
- services -> `/services`
- modules -> `/modules`
- audit -> `/audit-log`
- inventory_low_stock -> `/inventory`
- inventory_expiring -> `/inventory`
- draft_invoices -> `/invoices`
- unpaid_invoices -> `/invoices`
- api_keys -> `/api-keys`

Do not expose sensitive information.

Frontend:

Update Readiness page table to show “Otvori” or target label link when `target_path` exists.

Acceptance criteria:

- Readiness is actionable, not only informational.
- It remains read-only.

---

# Phase 3 — Add pilot evidence readiness check

Backend readiness should include a lightweight check for pilot evidence docs only if feasible without filesystem complexity.

Preferred simple approach:

Add a static readiness check:

- key: `human_pilot_evidence`
- label: `Human pilot evidence`
- status: warning
- message: `Provjerite docs/pilot_sessions prije v0.1-pilot taga.`
- action: `Ažurirati human pilot report, triage, ADR i Go/No-Go matrix.`
- target_path: `/readiness`

Do not attempt to parse markdown from backend unless already safe and simple.

Documentation should explain that pilot evidence remains documentation-governed for now.

Acceptance criteria:

- Readiness cockpit reminds maintainer that human evidence is still a release gate.

---

# Phase 4 — Improve Patient Workspace navigation from readiness and lists

Ensure:

- Patient list links clearly to `/patients/:id`.
- Appointment Workspace links to Patient Workspace.
- Patient Workspace links to related appointments.
- Patient Workspace links to related invoices.
- Patient Workspace audit tab works.

If already done, add smoke checks and do not over-refactor.

Acceptance criteria:

- user can move from readiness concern to relevant operational screen.

---

# Phase 5 — Add Invoice Workspace decision document

Do not build full invoice workspace unless very small and already mostly present.

Create:

`docs/INVOICE_WORKSPACE_PROPOSAL.md`

Include:

- why invoices should eventually become object-centered workspaces
- current limitation: invoice list/detail panel pattern
- proposed route: `/invoices/:id`
- required elements:
  - invoice header/status
  - patient link
  - appointment link
  - lines
  - payment history
  - fiscalization status
  - audit timeline
- migration plan from current Invoices page

Acceptance criteria:

- invoice workspace direction is defined but not overbuilt.

---

# Phase 6 — Add Readiness Cockpit tests

Backend tests:

- `/api/readiness` requires `audit.read` or appropriate permission
- readiness response contains summary
- readiness response contains demo guardrail check
- readiness response contains fiscalization check
- readiness response contains target paths for actionable checks
- status is blocked when demo guardrail fails if easy to test

Frontend smoke:

- Readiness page exists
- route `/readiness` exists
- readiness table shows next action
- readiness page shows demo mode and real-data allowed fields
- readiness page can render target links if string exists

Acceptance criteria:

- readiness cockpit regressions are caught.

---

# Phase 7 — Update pilot runbook to include readiness-first flow

Update:

`docs/PILOT_RUNBOOK.md`

Add a pre-demo step:

1. Open `/readiness`.
2. Confirm no critical blockers.
3. Review warnings.
4. Open linked screens for low-stock, unpaid invoices, API keys, or audit issues.
5. Only then run the pilot workflow.

Acceptance criteria:

- pilot starts from readiness cockpit.

---

# Phase 8 — Update known limitations and Go/No-Go matrix

Update:

- `docs/KNOWN_LIMITATIONS.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `docs/NEXT_ACTION_BEFORE_V0_1_TAG.md`

State:

- readiness cockpit is pilot support, not compliance certification
- human pilot evidence still governs v0.1-pilot tag decision
- readiness warnings may be acceptable for demo if documented
- readiness critical status blocks demo unless explicitly waived

Acceptance criteria:

- release governance and readiness cockpit tell the same story.

---

# Phase 9 — Architecture change proposal

Do not edit Architecture Bible directly.

Create:

`docs/ARCHITECTURE_CHANGE_PROPOSAL_READINESS_MODEL.md`

Propose adding to the Bible:

- readiness as read-only operational risk layer
- cockpit as pre-pilot entry point
- readiness checks must link to workspaces when possible
- readiness is not production/compliance approval

---

# Suggested commit sequence

1. `docs: add ASTRA readiness model`
2. `feat: add target links to readiness checks`
3. `feat: show readiness target links in cockpit`
4. `feat: add pilot evidence readiness reminder`
5. `test: cover readiness endpoint and cockpit smoke`
6. `docs: add invoice workspace proposal`
7. `docs: update pilot runbook for readiness-first flow`
8. `docs: align go no-go and limitations with readiness cockpit`
9. `docs: propose architecture bible readiness model update`

---

# Definition of done

This sprint is done when:

- Readiness Model document exists and is linked.
- Readiness checks include target paths where useful.
- Readiness UI links to relevant operational screens.
- Pilot evidence appears as a readiness reminder.
- Readiness tests/smoke checks exist.
- Pilot runbook starts with readiness cockpit.
- Invoice Workspace proposal exists.
- Go/No-Go docs clarify readiness vs human evidence.
- Architecture Bible is not silently changed; readiness proposal exists.

Do not add new clinical modules, real fiscalization, real-data enablement, external integrations, or new AI automation in this sprint.
