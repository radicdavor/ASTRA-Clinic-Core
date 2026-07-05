# ASTRA Clinic Core — v10 Pilot-to-Alpha Execution Plan

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak stanja nakon v9

V9 je značajan korak. Projekt je sada realno spreman za **zatvoreni pilot s demo podacima**, ali još uvijek nije spreman za realne pacijente.

U repozitoriju sada postoje ključni elementi pilot discipline:

- strukturirani GitHub issue template za pilot feedback
- `Real Data Readiness Checklist`
- `v0.1 Pilot Release Checklist`
- `Pilot Dry-Run Report Template`
- public runtime config endpoint `/api/public-config`
- demo/real-data flags
- demo banner vođen backend konfiguracijom
- testovi za data-only module manifest loader
- pilot runbook
- demo seed/reset
- pilot smoke test
- frontend smoke script

Moj zaključak: **projekt je prešao iz development MVP-a u pilot-candidate MVP.**

Ali “pilot-candidate” nije isto što i “alpha za stvarnu uporabu”. Prije bilo kakvog unošenja realnih podataka, treba proći kontrolirani dry-run, feedback, bug triage i v0.1-pilot release checklist.

## 2. Što je sada dobro

### 2.1 Public config i demo banner

Frontend više ne ovisi samo o build-time env varijabli za demo warning. `AppShell` čita `/api/public-config` i prikazuje banner ako je `demo_mode=true` ili `real_data_allowed=false`.

To je ispravna arhitektura jer backend ostaje izvor istine za sigurnosni status okruženja.

### 2.2 Real data readiness je eksplicitno blokiran

`REAL_DATA_READINESS_CHECKLIST.md` jasno kaže da realni pacijenti nisu dopušteni dok se ne riješe:

- GDPR/DPIA
- produkcijski hosting
- HTTPS
- jaki secret-i
- user management
- audit retention
- backup restore test
- prava fiskalizacija
- API key review

To mora ostati crvena linija.

### 2.3 Pilot feedback ima proces

Postoje dokumenti i issue template za prikupljanje pilot feedbacka. To je važnije nego se čini. Bez strukturiranog feedbacka pilot se pretvori u “meni se sviđa / meni se ne sviđa”.

Sada se feedback može klasificirati po:

- ulozi sudionika
- scenariju
- zadatku
- completed yes/no
- severity P0/P1/P2/P3
- real-data readiness concern

### 2.4 Module loader je testiran

`test_module_manifest_loader.py` sada pokriva:

- load one module
- idempotent reload
- service import by code
- update without duplicate
- material template import by service code + SKU
- missing inventory item skip
- invalid manifest validation
- no arbitrary Python execution

To znači da je put prema modularnosti sada sigurniji.

### 2.5 Pilot flow je demonstrabilan

Sustav sada ima radni flow:

1. dashboard
2. appointment detail
3. material consumption
4. stock movement
5. draft invoice
6. invoice issue
7. noop fiscalization warning
8. payment
9. purchase receiving
10. audit timeline

To je prvi pravi “clinic operations” lanac.

## 3. Što još nije dovoljno dobro

### 3.1 Nema stvarnog pilot rezultata

Imamo runbook i template, ali još nema stvarnog pilot dry-run izvještaja.

Sljedeći pravi korak nije novi feature, nego:

- pokrenuti pilot dry-run
- ispuniti report
- otvoriti issues
- riješiti P0/P1
- tek tada označiti v0.1-pilot

### 3.2 Frontend smoke nije pravi e2e

`pilot-smoke.mjs` je koristan, ali statički. On provjerava prisutnost ključnih datoteka/stringova, ne stvarnu interakciju korisnika.

Za v0.1-pilot je prihvatljivo, ali za alpha treba Playwright ili drugi e2e test koji klikne kroz barem login -> dashboard -> appointment detail.

### 3.3 Nema release taga ni release procedure u GitHubu

Postoji checklist, ali treba definirati:

- tag naming
- release notes template
- što ide u v0.1-pilot
- što je eksplicitno izvan scopea

### 3.4 Real-data guard je upozoravajući, ne blokirajući

Trenutno je dobro da sustav upozorava. Ali prije stvarne uporabe treba odlučiti treba li backend blokirati real-data unos dok `REAL_DATA_ALLOWED=true` nije eksplicitno postavljen.

Za demo/pilot s demo podacima ovo je dovoljno. Za realne pacijente nije.

### 3.5 Fiskalizacija je još Noop/stub

To je ispravno za demo. Ali billing UI mora još jasnije odvojiti:

- demo fiskalizacija
- stvarna fiskalizacija
- status neuspjeha
- ponovno slanje
- audit pokušaja

To nije prioritet prije pilot feedbacka, ali jest prije realne billing uporabe u Hrvatskoj.

## 4. Go / No-Go za v0.1-pilot

### Go za zatvoreni demo/pilot s demo podacima

Da, pod uvjetima:

- koristi se samo demo seed
- jasno je vidljiv demo banner
- pilot runbook se slijedi korak po korak
- feedback se bilježi u issue template
- nema unosa stvarnih pacijenata
- svi sudionici znaju da nema stvarne fiskalizacije

### No-Go za realne pacijente

Još uvijek ne.

Razlozi:

- nema formalne GDPR/DPIA odluke
- nema realne fiskalizacije
- nema production monitoring setupa
- nema production incident response plana
- user management nije dovoljno zreo za realnu ustanovu
- audit/access logging za čitanje podataka još nije dovoljno razrađen

## 5. Preporučeni v10 sprint

Naziv:

**v0.1 Pilot Release Sprint**

Cilj:

Ne dodavati velike funkcionalnosti. Cilj je pretvoriti trenutni pilot-candidate u označeni, demonstrabilni, dokumentirani `v0.1-pilot` release.

## 6. v10 Codex Master Prompt

```text
You are a senior full-stack architect, release manager and QA-minded maintainer.

You are working on radicdavor/ASTRA-Clinic-Core.

ASTRA Clinic Core has implemented v9. The project now has:

- backend and frontend MVP workflows
- CI
- tests
- public runtime config
- demo/real-data flags
- demo banner
- pilot feedback issue template
- real data readiness checklist
- pilot release checklist
- pilot dry-run report template
- module manifest loader tests
- pilot runbook
- demo seed/reset

The project is now a pilot-candidate with demo data only.

The next sprint is:

v0.1 Pilot Release Sprint

Main goal:
Prepare a clean, tagged v0.1-pilot release candidate and run one documented pilot dry-run using demo data.

Non-negotiable rules:
- Do not use real patient data.
- Do not implement real Croatian fiscalization yet.
- Do not add broad new medical modules.
- Do not add new AI mutation capabilities.
- Do not skip pilot feedback triage.

Phase 1 — Create release notes template

Add:

docs/RELEASE_NOTES_TEMPLATE.md

Must include:
- version
- date
- commit SHA
- release type: demo / pilot / alpha / production
- supported environment
- added
- changed
- fixed
- known limitations
- real data status
- fiscalization status
- migration notes
- rollback notes
- QA status
- open P0/P1 issues

Acceptance criteria:
- Future releases can be documented consistently.

Phase 2 — Add v0.1-pilot release notes draft

Add:

docs/releases/V0_1_PILOT_RELEASE_NOTES.md

Must state clearly:
- demo/pilot data only
- no real patient data
- no real Croatian fiscalization
- not certified EMR
- not certified medical device
- core demo flow supported
- known limitations

Acceptance criteria:
- Release notes are honest about maturity and risk.

Phase 3 — Add pilot dry-run report example

Add:

docs/pilot_sessions/V0_1_DRY_RUN_EXAMPLE.md

Use the dry-run report template and fill it with a sample run.

It should include:
- environment
- commit SHA placeholder
- participants placeholder
- demo steps
- expected results
- known limitations
- go/no-go decision placeholder

Acceptance criteria:
- Someone can copy this file and use it for a real pilot run.

Phase 4 — Add release validation script

Add a lightweight script:

scripts/validate_pilot_release.sh

It should check, where feasible:
- backend tests command documented
- frontend typecheck/build commands exist
- required docs exist
- pilot runbook exists
- feedback template exists
- real data readiness checklist exists
- v0.1 pilot checklist exists
- demo seed/reset modules exist

Do not overengineer.

Acceptance criteria:
- Maintainer can run one script before tagging v0.1-pilot.

Phase 5 — Update README with pilot status

Add a clear section:

Pilot status

Must say:
- Current stage: closed demo/pilot with demo data only
- Do not enter real patient data
- Run demo seed/reset
- Link to pilot runbook
- Link to real data readiness checklist
- Link to v0.1 pilot release checklist

Acceptance criteria:
- New visitor immediately understands project maturity.

Phase 6 — Add issue label guide or update existing one

Ensure docs/ISSUE_LABELS.md exists and includes:
- pilot:P0
- pilot:P1
- pilot:P2
- pilot:P3
- area:frontend
- area:backend
- area:inventory
- area:billing
- area:appointments
- area:audit
- area:security
- real-data-blocker

Acceptance criteria:
- Pilot feedback can be triaged consistently.

Phase 7 — Add go/no-go checklist to pilot runbook

Update docs/PILOT_RUNBOOK.md with a final Go/No-Go section:

Go if:
- no P0/P1 issues
- demo data only
- fiscalization shown as noop/stub
- audit trail visible
- material/inventory/billing workflows completed

No-Go if:
- data corruption
- permission bypass
- missing demo banner
- invoice/payment workflow blocked
- stock movement mismatch
- real-data confusion

Acceptance criteria:
- Pilot facilitator can make a clear decision.

Phase 8 — Add minimal known limitations page

Add:

docs/KNOWN_LIMITATIONS.md

Must include:
- not production ready
- no real patient data
- no real Croatian fiscalization
- limited frontend e2e
- module loader basic
- OpenEMR/Google Calendar integrations not implemented
- no full EMR charting
- no clinical decision support
- no prescription system

Acceptance criteria:
- Limitations are transparent and discoverable.

Phase 9 — Prepare v11 backlog from pilot feedback categories

Add:

docs/V11_BACKLOG_CANDIDATES.md

Organize possible future work by:
- P0/P1 pilot blockers
- frontend workflow refinement
- audit/security
- module system
- gastroenterology module v1
- Google Calendar integration
- OpenEMR integration
- AI receptionist integration
- Croatian fiscalization

Do not implement these yet.

Acceptance criteria:
- Future expansion is captured but deferred.

Suggested commit sequence:
1. docs: add release notes template
2. docs: add v0.1 pilot release notes draft
3. docs: add pilot dry-run example
4. chore: add pilot release validation script
5. docs: update readme with pilot status
6. docs: add issue label guide
7. docs: update pilot runbook go no-go section
8. docs: add known limitations
9. docs: add v11 backlog candidates

Definition of done:
- v0.1 pilot release docs exist
- pilot validation script exists
- README clearly says demo/pilot only
- pilot runbook has Go/No-Go
- limitations are explicit
- future backlog is deferred, not implemented
- no real patient data is enabled

After this sprint, manually run the pilot dry-run and fill out the report.
```

## 7. Manual pilot dry-run protocol

Before tagging v0.1-pilot:

1. Pull latest `main`.
2. Run `docker compose down -v` in demo environment only.
3. Run `docker compose up --build`.
4. Run `python -m app.demo.seed`.
5. Login as demo admin.
6. Follow `docs/PILOT_RUNBOOK.md` exactly.
7. Fill `docs/PILOT_DRY_RUN_REPORT_TEMPLATE.md` as a real report.
8. Convert findings to GitHub issues.
9. Label each issue P0/P1/P2/P3.
10. Do not tag v0.1-pilot if any P0/P1 remains open.

## 8. P0/P1 definitions for this project

### P0

- Data corruption in appointment, stock, invoice or payment workflow.
- Permission bypass allowing AI/API key to mutate inventory or billing without scope.
- Demo banner absent in demo mode.
- Real-data warning absent or misleading.
- Reset command can run in production.
- Invoice payment changes state incorrectly.
- Stock movement mismatch after material consumption or purchase receive.

### P1

- Core demo flow cannot be completed.
- Appointment detail fails for demo appointment.
- Material consumption fails despite sufficient stock.
- Purchase receiving fails despite valid line.
- Invoice issue/payment blocked despite valid data.
- Audit timeline missing for completed workflow.
- API key management exposes key hash or redisplays raw secret.

### P2

- Confusing label.
- Error message unclear.
- Extra clicks but workaround exists.
- Missing non-critical context.

### P3

- Cosmetic issue.
- Formatting/spacing.
- Minor Croatian wording.

## 9. What not to build yet

Do not build these before v0.1-pilot dry-run:

- broad Gastroenterology module v1
- OpenEMR integration
- Google Calendar sync
- real Croatian fiscalization
- AI receptionist
- voice agent
- patient portal
- prescriptions
- full EMR charting

Reason: the core operational loop must be proven first.

## 10. Strong recommendation

The best next action is not another feature sprint.

The best next action is:

1. Run the dry-run.
2. Open issues.
3. Fix P0/P1.
4. Tag `v0.1-pilot`.
5. Only then plan v11.

ASTRA is now at the point where real usage feedback is more valuable than architectural speculation.
