# ASTRA Clinic Core — v11 Closed Pilot Feedback Plan

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak nakon v10

V10 je uspješno pretvorio projekt iz “pilot candidate” stanja u sustav koji ima realan proces za `v0.1-pilot` release.

Sada postoje:

- release notes template
- draft `v0.1-pilot` release notes
- pilot release validation script
- pilot dry-run report template/example
- pilot feedback issue template
- real-data readiness checklist
- Go/No-Go logika u pilot runbooku
- jasno dokumentirane known limitations
- issue label discipline
- v11 backlog candidates

To znači da je sljedeći korak prvi put manje tehnički, a više operativan:

**izvesti kontrolirani pilot dry-run, prikupiti feedback i pretvoriti ga u prioritetni backlog.**

Moj stav: ASTRA je sada spremna za zatvoreni pilot s demo podacima. Nije spremna za realne pacijente.

## 2. Što je dobro nakon v10

### 2.1 Release notes postoje prije releasea

To je zreliji način rada. `docs/releases/V0_1_PILOT_RELEASE_NOTES.md` već jasno govori:

- demo/pilot data only
- no real patient data
- no real Croatian fiscalization
- not certified EMR
- not certified medical device
- core demo flow supported
- known limitations

To je dobro jer smanjuje rizik da netko projekt shvati ozbiljnije nego što smije.

### 2.2 Validation script postoji

`scripts/validate_pilot_release.sh` provjerava postojanje ključnih datoteka i tekstova:

- pilot runbook
- feedback template
- real data readiness checklist
- release checklist
- release notes
- dry-run example
- demo seed/reset
- issue template
- README pilot status
- frontend smoke/typecheck/build scripts

To je jednostavno, ali korisno.

### 2.3 Pilot release checklist postoji

`docs/V0_1_PILOT_RELEASE_CHECKLIST.md` postavlja razuman prag:

- CI green
- backend tests green
- frontend typecheck/build green
- pilot smoke green
- demo seed/reset verified
- no P0/P1 open
- real data still blocked
- fiscalization noop/stub
- demo banner visible
- API keys reviewed/deactivated

To je točno ono što treba prije taga.

## 3. Što sada nedostaje

### 3.1 Stvarni dry-run rezultat

Još uvijek nema stvarnog ispunjenog dry-run izvještaja nakon realnog prolaska kroz demo.

To je sada najvažniji artefakt koji nedostaje.

Treba napraviti:

- `docs/pilot_sessions/YYYY-MM-DD_v0.1_dry_run.md`
- popuniti commit SHA
- popuniti korake
- popisati bugove
- klasificirati severity
- donijeti Go/No-Go

### 3.2 Issues iz feedbacka

Dok feedback ne postane issue, ne postoji u procesu razvoja.

Svaki P0/P1/P2/P3 nalaz treba završiti kao issue s labelom.

### 3.3 Nema release tag procedure

Još treba odlučiti kako se označava release:

- tag: `v0.1-pilot`
- release title: `ASTRA Clinic Core v0.1-pilot`
- release notes: iz `docs/releases/V0_1_PILOT_RELEASE_NOTES.md`
- prerelease: yes

### 3.4 Nema odluke što ide u v11

V11 ne smije krenuti naslijepo. Mora nastati iz stvarnog pilot feedbacka.

Ako nema P0/P1, v11 može biti alpha-hardening. Ako ima P0/P1, v11 je blocker-fix sprint.

## 4. Preporuka

Sljedeći sprint treba biti:

**Closed Pilot Feedback Sprint**

Cilj:

1. izvesti dry-run
2. dokumentirati nalaze
3. otvoriti issues
4. riješiti P0/P1
5. pripremiti ili odgoditi tag `v0.1-pilot`
6. tek nakon toga odlučiti v11 backlog

## 5. V11 Codex Master Prompt

```text
You are a senior full-stack maintainer, release manager and pilot-feedback triage lead.

You are working on radicdavor/ASTRA-Clinic-Core.

ASTRA Clinic Core has completed v10 and is now a v0.1-pilot candidate for closed demo/pilot use with demo data only.

Current project state:

- core clinic operations demo flow exists
- appointment material consumption exists
- inventory/procurement workflow exists
- invoice issue/payment workflow exists
- audit timeline exists
- public config and demo warnings exist
- demo seed/reset exist
- pilot runbook exists
- release checklist exists
- release notes draft exists
- validation script exists
- pilot feedback issue template exists

The next sprint is:

Closed Pilot Feedback Sprint

Main goal:
Run a controlled pilot dry-run, record feedback, open/triage issues, fix P0/P1 blockers, and prepare or defer the v0.1-pilot tag.

Non-negotiable rules:
- Use demo data only.
- Do not enter real patient data.
- Do not implement real Croatian fiscalization.
- Do not expand broad medical modules.
- Do not add AI automations.
- Do not tag v0.1-pilot if any P0/P1 issue remains open.

Phase 1 — Create real dry-run report

Create a dated report:

docs/pilot_sessions/YYYY-MM-DD_v0.1_dry_run.md

Use docs/PILOT_DRY_RUN_REPORT_TEMPLATE.md.

Fill in:
- environment
- frontend URL
- backend URL
- database mode
- commit SHA placeholder or actual SHA if available
- participants
- demo script steps completed
- failed steps
- bugs found
- severity summary
- Go/No-Go decision

If no real human pilot was run yet, mark it clearly as “maintainer dry-run”.

Acceptance criteria:
- There is one real dry-run report, not only a template.

Phase 2 — Convert dry-run findings into issue list

Create:

docs/pilot_sessions/YYYY-MM-DD_issue_triage.md

Include table:

| ID | Severity | Area | Summary | Status | GitHub issue |
| --- | --- | --- | --- | --- | --- |

If no GitHub issues can be created automatically, include “to-create” placeholders.

Acceptance criteria:
- Every finding from dry-run has a triage line.

Phase 3 — Add P0/P1 blocker policy to release checklist

Update docs/V0_1_PILOT_RELEASE_CHECKLIST.md.

Add explicit rule:

- v0.1-pilot tag is blocked if any P0/P1 issue is open.
- P2 issues may remain only if documented in release notes.
- P3 issues may remain.

Acceptance criteria:
- Release checklist clearly blocks release on P0/P1.

Phase 4 — Update release notes from dry-run

Update docs/releases/V0_1_PILOT_RELEASE_NOTES.md.

Replace TBD fields where possible:
- Date
- Commit SHA placeholder if actual cannot be known
- QA status
- Pilot smoke status
- Known limitations from dry-run
- Open P0/P1 issues

Acceptance criteria:
- Release notes reflect actual dry-run status.

Phase 5 — Add v0.1 pilot tag instructions

Create:

docs/TAGGING_V0_1_PILOT.md

Include:

```bash
git status
git pull
git log -1 --oneline
./scripts/validate_pilot_release.sh
# run backend tests
# run frontend typecheck/build/smoke
git tag -a v0.1-pilot -m "ASTRA Clinic Core v0.1-pilot"
git push origin v0.1-pilot
```

Also include rollback:

```bash
git tag -d v0.1-pilot
git push origin :refs/tags/v0.1-pilot
```

Acceptance criteria:
- Maintainer can tag or remove the pilot tag safely.

Phase 6 — Add post-pilot decision record

Create:

docs/ADR/0001-v0-1-pilot-decision.md

ADR format:

- Status: Proposed / Accepted / Deferred
- Context
- Decision
- Consequences
- Real data status
- Fiscalization status
- Next milestone

Acceptance criteria:
- Pilot decision is captured as an architectural/product decision.

Phase 7 — Prepare v11 backlog from pilot outcome

Update or create:

docs/V11_BACKLOG_FROM_PILOT.md

Sections:

- P0/P1 blockers
- P2 usability fixes
- P3 polish
- alpha hardening candidates
- integrations deferred
- clinical modules deferred
- real-data blockers

Acceptance criteria:
- v11 work is driven by pilot results, not speculation.

Phase 8 — Add minimum alpha criteria

Create:

docs/ALPHA_READINESS_CRITERIA.md

Alpha readiness requires:

- no open P0/P1 pilot issues
- at least one completed pilot dry-run
- release notes updated
- audit trail accepted in pilot
- material/inventory workflow accepted in pilot
- invoice/payment demo accepted in pilot
- real-data checklist still blocking unless formally reviewed
- no real fiscalization claim

Acceptance criteria:
- Team knows when it is allowed to move from pilot to alpha planning.

Phase 9 — Optional: create GitHub issues for P0/P1 if tool access allows

If GitHub issue creation tooling is available, create issues for any P0/P1 from dry-run.
If not available, document issue payloads in the triage file.

Acceptance criteria:
- P0/P1 are actionable.

Suggested commit sequence:
1. docs: add real v0.1 pilot dry-run report
2. docs: add pilot issue triage table
3. docs: update pilot release checklist with blocker policy
4. docs: update v0.1 pilot release notes from dry-run
5. docs: add v0.1 pilot tagging instructions
6. docs: add pilot decision ADR
7. docs: add v11 backlog from pilot
8. docs: add alpha readiness criteria

Definition of done:
- dry-run report exists
- issue triage table exists
- release notes reflect dry-run
- P0/P1 blocker rule is explicit
- tag instructions exist
- ADR exists
- v11 backlog is derived from pilot
- alpha criteria are explicit
- no real patient data is enabled
```

## 6. What to do manually after this commit

1. Run `./scripts/validate_pilot_release.sh`.
2. Run the full pilot runbook.
3. Fill the dry-run report.
4. Create issue triage table.
5. Decide Go/No-Go.
6. If Go and no P0/P1: tag `v0.1-pilot`.
7. If No-Go: fix only blockers first.

## 7. Strong recommendation

At this stage, the highest-value work is not more code. It is disciplined use.

ASTRA has enough moving parts now that real feedback from a dry-run is more valuable than another feature layer. The next prompt should force execution discipline, not exploration.
