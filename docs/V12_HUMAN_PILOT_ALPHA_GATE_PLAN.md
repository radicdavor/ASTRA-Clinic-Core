# ASTRA Clinic Core — v12 Human Pilot Alpha Gate Plan

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak nakon v11

V11 je uspješno zatvorio procesnu stranu `v0.1-pilot` pripreme. Sada postoje stvarni artefakti za dry-run, issue triage, tagiranje, ADR i alpha readiness.

Najvažnije: V11 jasno pokazuje da je trenutačni dry-run bio **maintainer command-level dry-run**, a ne stvarni ljudski pilot. To je pošteno i važno.

Trenutno stanje:

- Command-level maintainer dry-run: prošao.
- Backend testovi: prošli u tom dry-runu.
- Frontend typecheck/smoke/build: prošli u tom dry-runu.
- P0/P1 iz command-level dry-runa: nema.
- Ljudski browser pilot: još nije napravljen.
- Tag `v0.1-pilot`: još nije sigurno napraviti bez odluke maintainer-a ili human dry-runa.
- Real patient data: i dalje zabranjen.

Moj zaključak: **projekt je spreman za human demo pilot s demo podacima, ali nije spreman za alpha planiranje dok se taj pilot ne odradi i ne triagira.**

## 2. Što je v11 dobro zaključao

### 2.1 Dry-run report postoji

`docs/pilot_sessions/2026-07-05_v0.1_dry_run.md` bilježi:

- lokalni Docker Compose demo environment
- lokalni PostgreSQL Docker service
- commit SHA na početku v11 rada
- maintainer/Codex dry-run
- backend pilot flow
- frontend smoke/typecheck/build
- backend Docker tests `64 passed`
- P0/P1: nema
- Go za sljedeći closed human pilot
- No-Go za tagiranje `v0.1-pilot` dok human pilot nije dovršen ili eksplicitno waived

To je ispravan i transparentan status.

### 2.2 Issue triage postoji

`docs/pilot_sessions/2026-07-05_issue_triage.md` sadrži DRYRUN-001 kao P2:

- human participant dry-run feedback još nije prikupljen
- command-level validation passed
- real usability feedback pending

To je točna klasifikacija. Nije P0/P1, ali je release governance blokator ako maintainer ne želi waive.

### 2.3 Tagging procedure postoji

`docs/TAGGING_V0_1_PILOT.md` definira:

- provjeru statusa
- validation script
- backend tests
- frontend typecheck/smoke/build
- `git tag -a v0.1-pilot`
- GitHub prerelease
- rollback tag procedure

To je dovoljno za uredno označavanje.

### 2.4 ADR postoji

`docs/ADR/0001-v0-1-pilot-decision.md` postavlja jasnu odluku:

- status: Proposed
- proceed to closed human pilot dry-run with demo data only
- do not tag dok report i issue triage nisu reviewed i nema P0/P1
- feature expansion remains deferred
- real patient data not allowed
- real Croatian fiscalization not implemented

Ovo je zrelo. Projekt sada ima product/architecture decision record, ne samo README.

### 2.5 Alpha readiness criteria postoje

`docs/ALPHA_READINESS_CRITERIA.md` kaže da alpha planning može početi tek kad:

- nema P0/P1
- postoji human pilot dry-run
- audit accepted
- material/inventory accepted
- invoice/payment accepted
- real-data checklist i dalje blokira real data osim formalne revizije
- noop/stub fiscalization nije pogrešno predstavljen
- P2/P3 su triagirani

To je pravi prag.

## 3. Što sada objektivno nedostaje

### 3.1 Human pilot report

Nedostaje stvarni dokument:

`docs/pilot_sessions/YYYY-MM-DD_human_pilot_01.md`

U njemu trebaju biti stvarni sudionici, uloge, opažanja i rezultati.

### 3.2 Human usability feedback

Nedostaje feedback od barem jedne osobe koja nije developer/Codex:

- recepcija
- liječnik
- sestra/inventory
- billing/admin

Bez toga ne znamo je li flow stvarno razumljiv.

### 3.3 Release Go/No-Go odluka

ADR je Proposed. Treba ga promijeniti u:

- Accepted: tag `v0.1-pilot`
- Deferred: potrebno popraviti P0/P1
- Waived: human pilot nije napravljen, ali maintainer eksplicitno dopušta tag uz poznati rizik

### 3.4 Stvarni issue backlog iz ljudskog feedbacka

Trenutačni backlog je dobar, ali je izveden iz maintainer dry-runa. Nakon ljudskog pilota treba nastati:

- P0/P1 blocker list
- P2 usability fixes
- P3 polish
- alpha hardening candidates

### 3.5 Minimalni human pilot script za facilitator-a

Runbook je dobar, ali treba još praktičniji facilitator sheet koji se može printati ili otvoriti na drugom ekranu tijekom sesije.

## 4. Preporučeni sljedeći korak

Sljedeći sprint treba biti:

**Human Pilot Alpha Gate Sprint**

Cilj:

1. pripremiti facilitator materijale
2. provesti ili simulirati human pilot
3. dokumentirati rezultate
4. ažurirati ADR
5. odlučiti tag/No-Go
6. napraviti alpha backlog iz stvarnog feedbacka

Ne treba dodavati nove funkcionalnosti dok ovo nije završeno.

## 5. V12 Codex Master Prompt

```text
You are a senior product-minded maintainer, release manager and pilot facilitator.

You are working on radicdavor/ASTRA-Clinic-Core.

ASTRA Clinic Core has completed v11. It has a maintainer command-level dry-run, release notes, tagging instructions, ADR, alpha readiness criteria, and pilot issue triage.

Current status:
- Command-level dry-run passed.
- No P0/P1 found in maintainer dry-run.
- Human participant browser pilot is still pending.
- Real patient data remains forbidden.
- Real Croatian fiscalization is not implemented.
- v0.1-pilot should not be tagged unless human pilot is completed or explicitly waived by maintainer.

The next sprint is:

Human Pilot Alpha Gate Sprint

Main goal:
Prepare and document the first human closed pilot using demo data only, then decide whether to tag v0.1-pilot or defer.

Non-negotiable rules:
- Demo data only.
- No real patient data.
- No real Croatian fiscalization.
- No broad new features.
- No new AI automation.
- No clinical module expansion.
- Do not change the v0.1-pilot scope unless a P0/P1 requires it.

Phase 1 — Create human pilot facilitator sheet

Create:

docs/pilot_sessions/HUMAN_PILOT_FACILITATOR_SHEET.md

It should be a practical one-page checklist for the person running the pilot.

Include:
- pre-session setup
- browser/device note
- demo login
- participant role
- exact tasks to ask participant to perform
- what facilitator should observe
- where to write issues
- stop conditions
- no real patient data warning
- no real fiscalization warning

Acceptance criteria:
- A non-developer facilitator can run the session.

Phase 2 — Create human pilot report template

Create:

docs/pilot_sessions/HUMAN_PILOT_REPORT_TEMPLATE.md

Sections:
- session metadata
- participant roles
- environment
- task completion table
- observed friction
- quotes/notes
- P0/P1/P2/P3 findings
- Go/No-Go recommendation
- links to GitHub issues
- real-data confusion observed yes/no
- fiscalization confusion observed yes/no

Acceptance criteria:
- Human pilot report is separate from maintainer dry-run.

Phase 3 — Create first human pilot report placeholder

Create:

docs/pilot_sessions/YYYY-MM-DD_human_pilot_01.md

Since the actual human session may not be run by Codex, create a placeholder using the report template with status:

Status: Pending human execution

Include:
- planned participant roles
- planned scenario
- required evidence
- criteria for completion

Acceptance criteria:
- Repository clearly tracks that human pilot is pending.

Phase 4 — Update ADR 0001 with explicit status options

Update:

docs/ADR/0001-v0-1-pilot-decision.md

Add a section:

Decision options:
1. Accepted — tag v0.1-pilot after human pilot passes with no P0/P1
2. Deferred — P0/P1 found or human pilot incomplete
3. Waived — maintainer explicitly permits tag without human pilot, documenting risk

Keep current status as Proposed unless human pilot results exist.

Acceptance criteria:
- ADR expresses exact release decision gate.

Phase 5 — Add v0.1-pilot Go/No-Go matrix

Create:

docs/V0_1_GO_NO_GO_MATRIX.md

Matrix columns:
- criterion
- evidence file
- status
- Go if
- No-Go if

Criteria:
- CI/tests
- frontend smoke/build
- maintainer dry-run
- human pilot
- P0/P1 issues
- real-data warnings
- fiscalization warning
- demo reset safety
- audit visibility
- material workflow
- invoice/payment workflow
- purchase receiving workflow

Acceptance criteria:
- Release decision can be made from one matrix.

Phase 6 — Create v0.1 pilot issue board protocol

Create:

docs/PILOT_ISSUE_BOARD_PROTOCOL.md

Include:
- label policy
- severity policy
- when to create issue
- who can close P0/P1
- definition of done for P0/P1
- how to defer P2/P3
- how to update release notes from issues

Acceptance criteria:
- Pilot issues have a governance process.

Phase 7 — Update v11 backlog with human-pilot dependency

Update:

docs/V11_BACKLOG_FROM_PILOT.md

Make it clear:
- Current backlog is provisional.
- Human pilot findings override maintainer speculation.
- No alpha hardening work starts until P0/P1 are reviewed.

Acceptance criteria:
- Backlog cannot be mistaken as final before human pilot.

Phase 8 — Create v12 actual Codex guardrail

Create:

docs/CODEX_GUARDRAILS_BEFORE_ALPHA.md

It should instruct future Codex sessions:
- inspect pilot reports before writing code
- do not add features if P0/P1 open
- prefer issue-linked changes
- cite evidence files in commit messages when possible
- keep real-data block intact
- keep noop fiscalization warning intact
- do not remove demo banner without formal readiness decision

Acceptance criteria:
- Future AI coding is constrained by pilot evidence.

Suggested commit sequence:
1. docs: add human pilot facilitator sheet
2. docs: add human pilot report template
3. docs: add pending human pilot report placeholder
4. docs: update pilot ADR with release decision options
5. docs: add v0.1 go no-go matrix
6. docs: add pilot issue board protocol
7. docs: clarify v11 backlog is provisional until human pilot
8. docs: add Codex guardrails before alpha

Definition of done:
- human pilot materials exist
- pending human pilot is explicit
- ADR has decision options
- Go/No-Go matrix exists
- issue board protocol exists
- backlog is explicitly provisional
- Codex guardrails prevent feature sprawl before alpha
- no real patient data is enabled
```

## 6. Actual next human action

After this commit, the human maintainer should:

1. Pick one participant, ideally non-developer.
2. Run the pilot with demo data.
3. Fill the human pilot report.
4. Create GitHub issues for findings.
5. Update the Go/No-Go matrix.
6. Update ADR 0001.
7. Decide tag/defer/waive.

## 7. Important recommendation

Do not let the project continue only by prompt iteration.

At this point, ASTRA needs friction from a real human using the flow. That friction is the next best requirement document.
