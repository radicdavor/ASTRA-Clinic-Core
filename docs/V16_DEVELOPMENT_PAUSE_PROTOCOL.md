# ASTRA Clinic Core — v16 Development Pause Protocol

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Zašto postoji ovaj dokument

V15 je treći uzastopni checkpoint koji potvrđuje istu stvar:

- human pilot nije odrađen
- status je pending
- ADR ostaje deferred
- `v0.1-pilot` tag ostaje blokiran
- nema maintainer waivera
- nema P0/P1 iz command-level dry-runa
- jedini otvoreni nalaz je P2 procesni dug: nema human usability feedbacka

To znači da je razvoj došao do jasne granice.

**Daljnji feature development prije ljudskog pilota je sada kontraproduktivan.**

Ovaj dokument definira pauzu razvoja i dopuštene aktivnosti dok se ne prikupi human pilot evidence.

## 2. Current canonical status

Canonical evidence files:

- `docs/pilot_sessions/2026-07-05_human_pilot_01.md`
- `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`
- `docs/NEXT_ACTION_BEFORE_V0_1_TAG.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `docs/ADR/0001-v0-1-pilot-decision.md`

Current status:

- Human pilot: Pending
- Maintainer dry-run: Passed
- Known P0/P1: None from command-level validation
- Known P2: Human pilot not executed
- ADR: Deferred
- v0.1-pilot tag: Blocked
- Real patient data: Forbidden
- Real Croatian fiscalization: Not implemented
- Broad feature work: Paused

## 3. Development pause rules

Until human pilot evidence exists, the following are paused:

- new clinical modules
- Google Calendar integration
- OpenEMR integration
- AI receptionist
- voice agent
- new AI mutation tools
- real Croatian fiscalization
- production deployment work
- real-data enablement
- broad UI redesign
- speculative backend expansion

Allowed work during pause:

- fix confirmed P0/P1 blockers
- fix CI breakage
- fix test failures
- fix security-critical issue
- improve pilot documentation
- prepare human pilot logistics
- update evidence files truthfully
- add issues from actual pilot findings

## 4. Human evidence requirement

Before any new product scope is started, the repository must contain one of the following:

### Option A — Completed human pilot

`docs/pilot_sessions/2026-07-05_human_pilot_01.md` must show:

- Status: Completed
- participant role
- browser/device
- task completion table
- observed friction
- P0/P1/P2/P3 findings
- real-data confusion Yes/No
- fiscalization confusion Yes/No
- Go/No-Go recommendation

### Option B — Explicit maintainer waiver

ADR 0001 must show:

- Status: Waived
- why human pilot was waived
- what risk is accepted
- why `v0.1-pilot` can be tagged anyway
- when human pilot will still be done

No other state allows scope expansion.

## 5. Decision tree

### Human pilot completed, no P0/P1

Then:

1. update triage
2. update Go/No-Go matrix
3. update ADR to Accepted
4. update release notes
5. update release checklist
6. tag `v0.1-pilot` if maintainer approves
7. start alpha hardening planning

### Human pilot completed, P0/P1 exists

Then:

1. keep ADR Deferred
2. create P0/P1 blocker fix plan
3. fix only P0/P1
4. retest affected workflow
5. rerun human pilot step or targeted validation
6. only then reconsider tag

### Human pilot not completed

Then:

1. keep ADR Deferred
2. keep tag blocked
3. do not add features
4. schedule pilot session
5. update `NEXT_ACTION_BEFORE_V0_1_TAG.md`

### Human pilot waived

Then:

1. update ADR to Waived
2. update release notes with risk
3. update Go/No-Go matrix as Waived
4. keep real-data block
5. tag only if maintainer explicitly chooses

## 6. Practical checklist for the maintainer

Before asking Codex for more code, answer:

1. Has the human pilot been completed?
2. Is the report filled with real participant feedback?
3. Are there any P0/P1 issues?
4. Is the ADR Accepted, Deferred or Waived?
5. Is `v0.1-pilot` tag decision documented?
6. Are real patient data still blocked?
7. Is fiscalization still clearly marked as noop/stub?

If answer to 1 is No, do not request new features.

## 7. v16 Codex Master Prompt

```text
You are a senior release governance assistant for radicdavor/ASTRA-Clinic-Core.

The project has completed v15.

Current known state:
- human pilot is still pending
- ADR 0001 is Deferred
- v0.1-pilot tag is blocked
- real patient data is forbidden
- real Croatian fiscalization is not implemented
- no P0/P1 blockers are known from command-level validation
- P2 process debt remains: human usability feedback is missing

This is not a feature sprint.

This is a Development Pause / Human Evidence Gate.

Your task is to inspect evidence and update only governance documents unless a real P0/P1 bug is provided.

Non-negotiable rules:
- Do not add features.
- Do not add integrations.
- Do not expand clinical modules.
- Do not add AI automations.
- Do not enable real patient data.
- Do not imply real fiscalization.
- Do not fabricate pilot results.

Phase 1 — Inspect canonical evidence

Read:

docs/pilot_sessions/2026-07-05_human_pilot_01.md
docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md
docs/NEXT_ACTION_BEFORE_V0_1_TAG.md
docs/V0_1_GO_NO_GO_MATRIX.md
docs/ADR/0001-v0-1-pilot-decision.md

Determine state:
- Pending
- Completed
- Deferred
- Waived
- Accepted

Phase 2 — If still pending

Do not change code.
Do not add features.

Update or create:

docs/NEXT_ACTION_BEFORE_V0_1_TAG.md

to keep the exact next action clear:
- run human pilot
- fill report
- triage findings
- update ADR

Optionally update:

docs/V0_1_GO_NO_GO_MATRIX.md

to keep human pilot row Pending.

Phase 3 — If completed

If actual human pilot evidence exists, update:
- triage
- Go/No-Go matrix
- ADR
- release notes
- release checklist

If no P0/P1 and Go recommendation exists, prepare `docs/V0_1_TAG_READY.md`.
If P0/P1 exist, prepare `docs/P0_P1_BLOCKER_FIX_PLAN.md`.

Phase 4 — If waived

If maintainer explicitly waived human pilot, update:
- ADR to Waived
- release notes with waiver risk
- Go/No-Go matrix with waiver
- tag readiness only if maintainer approves

Phase 5 — Preserve safety

Always confirm:
- real patient data remains blocked
- `REAL_DATA_ALLOWED=false` remains default
- noop/stub fiscalization warning remains
- demo banner remains

Suggested commit sequence:
1. docs: inspect human pilot evidence gate
2. docs: update next action before v0.1 tag
3. docs: update go no-go matrix if evidence changed
4. docs: update ADR if decision changed
5. docs: prepare tag ready or blocker plan only if evidence supports it

Definition of done:
- repository truthfully reflects pilot status
- no features added
- tag remains blocked unless evidence supports Go/Waiver
- next human action is explicit
- safety guards remain intact
```

## 8. What to tell future contributors

ASTRA is not blocked because of missing code.

ASTRA is blocked because the core flow has not yet been observed with a human participant.

That is a healthy block.

It prevents building the wrong next layer.

## 9. Minimal action list

Do this next:

1. Schedule 30-45 minutes with one participant.
2. Run demo environment.
3. Follow facilitator sheet.
4. Fill human pilot report.
5. Triage findings.
6. Decide Accepted / Deferred / Waived.
7. Only then ask Codex for the next change.

## 10. Final position

No more feature prompts before human evidence.

No more architecture expansion before human evidence.

No more module expansion before human evidence.

The next best requirement is a person using the system.
