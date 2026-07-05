# ASTRA Clinic Core — v13 Human Pilot Execution Kit

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak nakon v12

V12 je dobro zatvorio pripremu za ljudski pilot. Projekt sada ima sve što je potrebno da se zatvoreni human pilot provede na kontroliran, dokumentiran i siguran način — s demo podacima.

Najvažnije:

- postoji facilitator sheet
- postoji human pilot report template
- postoji pending human pilot report placeholder
- postoji Go/No-Go matrix
- postoje Codex guardrails prije alpha faze
- ADR 0001 jasno govori da je human pilot gate prije taga
- real patient data je i dalje blokiran
- real Croatian fiscalization nije implementirana

Moj stav: **nema više smisla pisati nove razvojne promptove prije stvarnog ljudskog pilot prolaza**.

Sljedeća vrijednost neće doći iz novog featurea. Doći će iz promatranja čovjeka kako pokušava koristiti ASTRA flow.

## 2. Što je v12 dobro zaključao

### 2.1 Facilitator sheet je praktičan

`docs/pilot_sessions/HUMAN_PILOT_FACILITATOR_SHEET.md` sadrži:

- pre-session setup
- sigurnosna upozorenja
- demo login
- ulogu sudionika
- točne zadatke za sudionika
- što promatrati
- gdje pisati issues
- stop conditions

Ovo je dovoljno da pilot ne ovisi samo o developeru koji poznaje sustav.

### 2.2 Human pilot report template je odvojen od maintainer dry-runa

To je bitno. Command-level dry-run nije isto što i ljudski pilot. Template sada traži:

- session metadata
- participant role
- environment
- task completion
- observed friction
- quotes/notes
- P0/P1/P2/P3 findings
- Go/No-Go recommendation
- confusion checks za real-data i fiscalization

To je prava struktura.

### 2.3 Pending human pilot placeholder pošteno dokumentira da pilot nije odrađen

`docs/pilot_sessions/2026-07-05_human_pilot_01.md` eksplicitno kaže:

- Status: Pending human execution
- Do not treat this as completed evidence
- required evidence for completion

To sprječava samozavaravanje.

### 2.4 Go/No-Go matrix je dobar release control

`docs/V0_1_GO_NO_GO_MATRIX.md` jasno odvaja:

- maintainer dry-run: prošao
- human pilot: pending
- P0/P1: nema iz maintainer dry-runa
- audit/material/invoice/purchase workflow: pending human confirmation

To je točno stanje.

### 2.5 Codex guardrails su ispravne

`docs/CODEX_GUARDRAILS_BEFORE_ALPHA.md` budućim Codex sesijama kaže da prije pisanja koda moraju pregledati:

- pilot sessions
- Go/No-Go matrix
- v11 backlog
- P0/P1 status

I zabranjuje feature-sprawl ako postoje P0/P1.

To je jako važno za AI-assisted development.

## 3. Aktualna odluka

### Go

Go za **zatvoreni human pilot s demo podacima**.

### No-Go

No-Go za:

- real patient data
- production use
- real Croatian fiscalization
- broad clinical module expansion
- new AI mutation features
- alpha planning prije human pilot reporta

### Conditional

Tag `v0.1-pilot` je dopušten tek ako:

1. human pilot report bude completed, ili maintainer formalno waivea human pilot
2. nema otvorenih P0/P1
3. release checklist prođe
4. ADR 0001 se ažurira iz Proposed u Accepted ili Waived
5. release notes dobiju stvarni commit SHA/date/QA status

## 4. Human pilot execution protocol

### 4.1 Priprema prije sesije

1. Pull latest `main`.
2. Pokreni demo lokalno:

```bash
docker compose down -v
docker compose up --build
```

3. Seed demo data:

```bash
docker compose exec backend python -m app.demo.seed
```

4. Provjeri public config:

```bash
curl http://localhost:8000/api/public-config
```

Mora biti:

```json
"real_data_allowed": false
```

5. Otvori frontend:

```text
http://localhost:5173
```

6. Provjeri da je demo banner vidljiv.
7. Otvori facilitator sheet.
8. Otvori human pilot report template.
9. Dogovori da se ne unose stvarni podaci.

### 4.2 Sudionik

Minimalno jedan sudionik koji nije developer.

Idealno:

- recepcija ili administracija za dashboard/račun
- liječnik/sestra za appointment/material flow
- inventory osoba za purchase receiving

Ako je samo jedan sudionik dostupan, neka prođe sve role kao “clinic operator”.

### 4.3 Zadaci za sudionika

Sudionik treba sam pokušati:

1. prijaviti se
2. pronaći današnji demo termin
3. otvoriti appointment detail
4. promijeniti status termina
5. učitati material suggestion
6. završiti appointment s potrošnjom materijala
7. pronaći stock movement
8. kreirati draft invoice
9. izdati invoice
10. objasniti što znači noop/demo fiscalization warning
11. evidentirati uplatu
12. zaprimiti purchase order line
13. pronaći audit trail
14. objasniti vidi li tko je što napravio

Facilitator ne smije odmah pomagati osim ako korisnik zapne dulje od 30-60 sekundi ili ako postoji rizik pogrešnog unosa.

### 4.4 Što promatrati

Bilježiti:

- gdje sudionik zastaje
- koji label ne razumije
- koji gumb izgleda opasno
- jesu li warningi jasni
- razumije li razliku demo fiskalizacija vs stvarna fiskalizacija
- razumije li da nema stvarnih pacijenata
- razumije li zaliha/material consumption logiku
- razumije li payment status
- može li pronaći audit trail

### 4.5 Stop conditions

Odmah zaustaviti pilot ako:

- sudionik želi unijeti stvarne podatke
- demo banner nije vidljiv
- fiscalization warning nije vidljiv
- stock movement ne odgovara potrošnji
- invoice/payment status se krivo promijeni
- permission bypass se posumnja
- sustav se ponaša destruktivno ili nepredvidivo

## 5. Human pilot report — minimalni kriterij prihvaćanja

Report mora imati:

- stvarni datum/vrijeme
- facilitator
- participant role
- browser/device
- commit SHA
- task completion table
- observed friction
- P0/P1/P2/P3 findings
- real-data confusion yes/no
- fiscalization confusion yes/no
- Go/No-Go recommendation
- issue links ili to-create placeholders

Bez toga human pilot nije završen.

## 6. P0/P1 pravila

### P0 — release block

- data corruption
- stock mismatch
- invoice/payment incorrect state
- permission bypass
- API key can perform unauthorized destructive action
- reset can affect production
- demo banner missing
- user thinks real data is allowed
- user thinks fiscalization is real

### P1 — release block

- participant cannot complete core flow
- appointment detail blocks workflow
- material consumption blocked despite sufficient stock
- invoice issue/payment blocked despite valid data
- purchase receiving blocked despite valid data
- audit trail unavailable for completed workflow

### P2 — may defer with release note

- confusing label
- too many clicks
- unclear error message
- workaround exists

### P3 — may defer

- cosmetic
- layout
- minor wording

## 7. v13 Codex Master Prompt

```text
You are a senior product maintainer, QA facilitator and release manager.

You are working on radicdavor/ASTRA-Clinic-Core.

ASTRA Clinic Core has completed v12. The repository now has all materials needed to run a closed human pilot with demo data only:

- facilitator sheet
- human pilot report template
- pending human pilot report placeholder
- Go/No-Go matrix
- pilot issue triage process
- ADR 0001
- alpha readiness criteria
- Codex guardrails before alpha
- real data readiness checklist
- demo/public config warnings
- release notes and tagging docs

The next sprint is:

Human Pilot Execution and Release Decision Sprint

Main goal:
Turn the pending human pilot into either:
1. an accepted v0.1-pilot release decision, or
2. a deferred release with P0/P1 fixes clearly listed.

Non-negotiable rules:
- Demo data only.
- No real patient data.
- No real Croatian fiscalization.
- No new broad features.
- No clinical module expansion.
- No new AI mutation capabilities.
- Do not tag v0.1-pilot if P0/P1 remain open.

Phase 1 — Update pending human pilot report after actual session

Update:

docs/pilot_sessions/2026-07-05_human_pilot_01.md

If an actual human pilot was completed, change status from pending to completed and fill:
- participant role
- browser/device
- commit SHA
- task completion table
- observed friction
- findings
- real-data confusion
- fiscalization confusion
- Go/No-Go

If the actual human pilot was not completed, do not fabricate results. Keep status pending and state why.

Acceptance criteria:
- Report truthfully reflects pilot status.

Phase 2 — Update issue triage from human pilot

Create or update:

docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md

Include each finding:
- ID
- severity
- area
- summary
- issue link or to-create
- owner
- status
- release decision impact

Acceptance criteria:
- Every human pilot finding is triaged.

Phase 3 — Update Go/No-Go matrix

Update:

docs/V0_1_GO_NO_GO_MATRIX.md

Set status for:
- human pilot
- audit visibility
- material workflow
- invoice/payment workflow
- purchase receiving workflow
- real-data warnings
- fiscalization warnings

Acceptance criteria:
- Matrix reflects actual pilot evidence.

Phase 4 — Update ADR 0001

Update:

docs/ADR/0001-v0-1-pilot-decision.md

Choose one status:
- Accepted: tag v0.1-pilot after human pilot passed with no P0/P1
- Deferred: P0/P1 found or human pilot incomplete
- Waived: maintainer explicitly permits tag without human pilot and documents risk

Acceptance criteria:
- ADR status is no longer ambiguous after pilot decision.

Phase 5 — Update v0.1-pilot release notes

Update:

docs/releases/V0_1_PILOT_RELEASE_NOTES.md

Fill:
- date
- commit SHA
- QA status
- dry-run/human pilot status
- open P0/P1 issues
- accepted P2/P3 limitations
- real-data status
- fiscalization status

Acceptance criteria:
- Release notes are ready for GitHub prerelease if decision is Go.

Phase 6 — Create issue payloads for findings

If direct GitHub issue creation is not available, create:

docs/pilot_sessions/2026-07-05_issue_payloads.md

Each issue payload should include:
- title
- labels
- body
- severity
- reproduction steps
- expected behavior
- actual behavior
- release impact

Acceptance criteria:
- Findings can be copied into GitHub issues.

Phase 7 — If P0/P1 exist, create blocker fix plan

If any P0/P1 exists, create:

docs/P0_P1_BLOCKER_FIX_PLAN.md

Include:
- blocker summary
- owner
- proposed fix
- tests required
- release impact
- retest steps

If no P0/P1 exists, create the file with “No P0/P1 blockers identified” and keep it short.

Acceptance criteria:
- Release-blocking work is explicit.

Phase 8 — Prepare alpha candidate backlog only after decision

Update:

docs/V11_BACKLOG_FROM_PILOT.md

If release is Go:
- move P2/P3 items into alpha hardening candidates
- keep integrations deferred
- keep broad modules deferred unless justified by pilot

If release is Deferred:
- keep focus on P0/P1 fixes only

Acceptance criteria:
- Next sprint follows evidence, not speculation.

Suggested commit sequence:
1. docs: update human pilot report with actual status
2. docs: add human pilot triage table
3. docs: update go no-go matrix from pilot evidence
4. docs: update pilot ADR decision
5. docs: update v0.1 pilot release notes
6. docs: add pilot issue payloads
7. docs: add p0 p1 blocker fix plan
8. docs: update backlog from pilot evidence

Definition of done:
- human pilot status is truthful
- findings are triaged
- Go/No-Go matrix updated
- ADR decision updated
- release notes updated
- P0/P1 plan exists
- backlog is evidence-based
- no real patient data is enabled
```

## 8. What the maintainer should do now

Do not ask Codex for another feature before this happens:

1. Run the human pilot.
2. Fill the report.
3. Triage issues.
4. Decide Accepted / Deferred / Waived.
5. Only then tag or fix blockers.

## 9. Strong recommendation

This project has reached a maturity point where further architecture without human observation is lower value.

The next best requirement is not another imagined feature.

The next best requirement is watching one real clinic user try to complete the demo flow.
