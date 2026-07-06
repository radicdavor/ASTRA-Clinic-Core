# Codex master prompt v22 — Operational Evidence Loop Sprint

Use this prompt in Codex after V21 has been implemented or partially implemented.

---

You are a senior full-stack architect, healthcare workflow designer, QA maintainer and product governance engineer.

Before making changes, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md`
- `docs/ASTRA_DESIGN_SYSTEM.md`
- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/ARCHITECTURE_REVIEW_V22.md`

## Sprint name

**Operational Evidence Loop Sprint**

## Main goal

Close the loop between:

`Readiness → Workspace → Action → Audit → Pilot/Release evidence`

ASTRA should not merely show warnings. It should guide the user from a readiness issue to the correct workspace, help them understand the action, preserve audit evidence, and make release/pilot decisions clearer.

## Non-negotiable rules

- Do not enable real patient data.
- Do not implement real Croatian fiscalization.
- Do not add new clinical modules.
- Do not add Google Calendar/OpenEMR or other external integrations.
- Do not add AI receptionist or new AI mutation workflows.
- Keep readiness endpoint read-only.
- Keep demo warnings visible.
- Keep noop/stub fiscalization warning visible.
- Keep Architecture Bible stable unless maintainer explicitly requests an edit.

---

# Phase 1 — Add readiness decision impact

Backend:

Extend `ReadinessCheck` schema with optional fields:

- `decision_impact: "none" | "review" | "blocks_demo" | "blocks_release"`
- `severity_reason: str | None`

Rules:

- demo guardrail failure: `blocks_demo`
- real_data_allowed=true in demo context: `blocks_demo`
- noop fiscalization: `review`, not blocker for demo
- no provider/room/service: `blocks_demo`
- low stock: `review`, unless current logic already critical
- active API keys: `review`
- missing human pilot evidence: `blocks_release`, not necessarily blocks demo

Update `ReadinessOut` if needed.

Frontend:

Readiness table should show a clear badge:

- “Info”
- “Pregledati”
- “Blokira demo”
- “Blokira release”

Acceptance criteria:

- Readiness no longer only says ok/warning/critical.
- It also explains release/demo impact.

---

# Phase 2 — Strengthen readiness target links

Ensure every actionable readiness check has:

- `target_path`
- `target_label`

Examples:

- patients -> `/patients`
- services -> `/services`
- modules -> `/modules`
- audit -> `/audit-log`
- low stock -> `/inventory`
- expiring stock -> `/inventory`
- draft invoices -> `/invoices`
- unpaid invoices -> `/invoices`
- api_keys -> `/api-keys`
- human_pilot_evidence -> no real UI target yet; use `/readiness` and action text pointing to docs

Frontend:

- Render target links consistently.
- Make it obvious what to open next.

Acceptance criteria:

- User can go from readiness issue to inspection screen in one click when a screen exists.

---

# Phase 3 — Add Readiness Detail Panel

Frontend Readiness page:

When user clicks/selects a readiness row, show a detail panel with:

- label
- status
- decision impact
- message
- severity reason
- next action
- target link if available
- whether this is demo blocker, release blocker or informational

Keep it simple; no modal required.

Acceptance criteria:

- Readiness page becomes a cockpit, not only a table.

---

# Phase 4 — Patient Workspace Summary Strip

Patient Workspace currently shows identity, metrics, appointments, invoices and audit.

Add a compact summary strip:

- Last appointment date/status if available
- Next appointment date/status if available
- Open invoice count or unpaid total if available
- Duplicate warning count if available
- OIB present yes/no

Do not implement heavy clinical episode logic yet.

Acceptance criteria:

- Patient Workspace answers: “what is the current state of this patient?”

---

# Phase 5 — Workspace Audit Readability

Improve `AuditTimeline` or add helper functions:

- human-readable action label
- entity label
- actor display fallback
- request ID shown compactly
- collapsible before/after JSON if already present
- link to related entity if route exists and safe

Do not remove raw audit data. Make it easier to understand.

Acceptance criteria:

- Workspace audit timeline is understandable to non-developer pilot users.

---

# Phase 6 — Operational Evidence Loop documentation

Create:

`docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`

Explain:

1. Readiness identifies operational risk.
2. User follows target link to workspace.
3. User performs guided action using ActionButton/HelpHint.
4. Backend writes audit.
5. Readiness improves or remains warning.
6. Pilot/release evidence is updated.

Include examples:

- low stock → inventory → purchase receive → stock movement/audit → readiness review
- draft invoice → invoice UI → issue/payment → audit → readiness review
- missing human pilot evidence → pilot docs → ADR/Go-No-Go update

Acceptance criteria:

- The operating model is documented.

---

# Phase 7 — Readiness-first pilot runbook

Update:

`docs/PILOT_RUNBOOK.md`

Add or strengthen the flow:

1. Open `/readiness`.
2. Review blockers and warnings.
3. Follow target links for inspection.
4. Decide whether warnings are acceptable for demo.
5. Only then start patient/appointment/material/invoice/purchase workflow.
6. After workflow, return to `/readiness` and audit.

Acceptance criteria:

- Pilot runbook starts from readiness cockpit.

---

# Phase 8 — Tests and smoke

Backend tests:

- readiness includes decision_impact
- readiness includes target links
- missing core setup can block demo
- noop fiscalization is review/warning, not demo blocker
- human pilot evidence is release blocker/review reminder depending chosen wording

Frontend smoke:

- Readiness page displays target links
- Readiness page displays decision impact labels
- Patient Workspace summary strip exists
- AuditTimeline contains human-readable action label logic

Acceptance criteria:

- CI catches regressions in the operational evidence loop.

---

# Phase 9 — Invoice Workspace proposal refinement

If `docs/INVOICE_WORKSPACE_PROPOSAL.md` exists, update it.

If not, create it.

Add a section:

- why invoice readiness checks should eventually open `/invoices/:id` or filtered invoice workspace
- how invoice issue/payment audit should appear in Invoice Workspace
- why this is deferred until readiness-workspace loop is stable

Do not build full invoice workspace unless already very small.

---

# Phase 10 — Architecture change proposal

Create:

`docs/ARCHITECTURE_CHANGE_PROPOSAL_OPERATIONAL_EVIDENCE_LOOP.md`

Propose adding to Architecture Bible:

- Readiness is the pre-demo cockpit.
- Workspaces are where risks are inspected/resolved.
- ActionButton/HelpHint guide the action.
- Audit is the evidence.
- Pilot/release docs record the decision.

Do not edit the Bible directly.

---

# Suggested commit sequence

1. `feat: add readiness decision impact metadata`
2. `feat: link readiness checks to operational screens`
3. `feat: add readiness detail panel`
4. `feat: add patient workspace summary strip`
5. `feat: improve audit timeline readability`
6. `docs: add operational evidence loop model`
7. `docs: update pilot runbook for readiness first workflow`
8. `test: cover readiness decision impact and cockpit smoke`
9. `docs: refine invoice workspace proposal`
10. `docs: propose operational evidence loop bible update`

---

# Definition of done

This sprint is done when:

- Readiness checks show status and decision impact.
- Readiness checks link to relevant screens where possible.
- Readiness page has an inspection/detail panel.
- Patient Workspace has a summary strip.
- Audit timeline is more readable.
- Operational Evidence Loop doc exists.
- Pilot runbook uses readiness-first workflow.
- Tests/smoke cover readiness-to-workspace behavior.
- Architecture Bible is not silently changed; proposal exists.

Do not add new clinical modules, external integrations, real fiscalization, real-data enablement or new AI automation.
