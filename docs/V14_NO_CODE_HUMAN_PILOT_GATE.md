# ASTRA Clinic Core — v14 No-Code Human Pilot Gate

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak nakon v13

V13 je napravio ispravnu stvar: nije fabricirao human pilot rezultate.

Stanje je sada jasno:

- maintainer command-level dry-run je prošao
- backend i frontend provjere su prošle u prethodnim dry-run artefaktima
- human pilot je i dalje pending
- ADR 0001 je prebačen u `Deferred`
- tag `v0.1-pilot` je blokiran dok human pilot nije dovršen ili dok maintainer eksplicitno ne napravi waiver
- jedini trenutno poznati otvoreni nalaz je P2 procesni dug: nema human usability feedbacka
- real patient data je i dalje zabranjen
- real Croatian fiscalization nije implementirana

Moj stav: **ovo je sada točka na kojoj treba prestati tražiti novi razvojni kod od Codexa dok se ne odradi human pilot.**

Daljnje pisanje novih razvojnih promptova bez stvarnog ljudskog prolaza samo će povećavati kompleksnost bez validacije.

## 2. Što je trenutno Go

Dozvoljeno je:

- pokrenuti closed human pilot s demo podacima
- koristiti demo seed/reset
- koristiti facilitator sheet
- koristiti human pilot report template
- koristiti pilot feedback issue template
- otvoriti issues iz nalaza
- popraviti P0/P1 ako se nađu
- tagirati `v0.1-pilot` samo ako gate prođe ili se waiver jasno dokumentira

## 3. Što je trenutno No-Go

Nije dopušteno:

- real patient data
- produkcijska uporaba
- stvarna hrvatska fiskalizacija
- broad Gastro module v1
- Google Calendar/OpenEMR integracije
- AI receptionist
- novi AI mutation flows
- širenje medicinskih modula
- tag `v0.1-pilot` bez human pilot completion ili formalnog waivera

## 4. Zašto je ovo važno

Projekt je već prošao fazu “treba još arhitekture”. Sada treba stvaran otpor korisnika:

- hoće li netko razumjeti workflow bez objašnjavanja?
- vidi li korisnik demo banner?
- razumije li Noop fiskalizaciju?
- zna li što znači skidanje materijala sa zalihe?
- može li pronaći račun?
- može li zaprimiti robu?
- može li objasniti audit timeline?

To se ne može riješiti još jednim tehničkim promptom. To se rješava pilotom.

## 5. Human Pilot Execution Bundle

Prije sesije otvoriti ova tri dokumenta:

1. `docs/pilot_sessions/HUMAN_PILOT_FACILITATOR_SHEET.md`
2. `docs/pilot_sessions/HUMAN_PILOT_REPORT_TEMPLATE.md`
3. `docs/V0_1_GO_NO_GO_MATRIX.md`

Nakon sesije ažurirati:

1. `docs/pilot_sessions/2026-07-05_human_pilot_01.md`
2. `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`
3. `docs/ADR/0001-v0-1-pilot-decision.md`
4. `docs/releases/V0_1_PILOT_RELEASE_NOTES.md`
5. `docs/V11_BACKLOG_FROM_PILOT.md`

## 6. Minimalni human pilot scenarij

Participant mora pokušati samostalno:

1. prijaviti se
2. pronaći današnji demo termin
3. otvoriti appointment detail
4. promijeniti status termina
5. učitati prijedlog materijala
6. završiti termin uz potrošnju materijala
7. provjeriti stock movement
8. kreirati nacrt računa
9. izdati račun
10. prepoznati da je fiskalizacija demo/noop
11. evidentirati uplatu
12. zaprimiti narudžbenicu
13. pregledati audit log/timeline
14. objasniti što je napravljeno i gdje se to vidi

Ako participant ne može samostalno doći do koraka bez pomoći, to je nalaz, ne greška participant-a.

## 7. Facilitator pravila

Facilitator smije:

- pročitati početni scenarij
- podsjetiti da se koriste demo podaci
- zaustaviti unos stvarnih podataka
- pomoći ako postoji sigurnosni rizik
- postaviti pitanje “što očekujete da će se dogoditi ako kliknete ovo?”

Facilitator ne smije:

- voditi korisnika klik-po-klik od početka
- objašnjavati svaki label prije nego korisnik pokuša
- sakriti zbunjenost korisnika
- klasificirati problem kao “korisnička greška” ako UI nije jasan

## 8. Kriteriji za odluku nakon human pilota

### Accepted

Može se tagirati `v0.1-pilot` ako:

- human pilot je dovršen
- nema P0/P1
- P2/P3 su triagirani
- demo banner je bio vidljiv
- participant nije mislio da su realni pacijenti dopušteni
- participant nije mislio da je fiskalizacija stvarna
- core flow je dovršen
- release notes su ažurirane
- ADR je Accepted

### Deferred

Tag se odgađa ako:

- human pilot nije dovršen
- postoji P0/P1
- participant nije mogao dovršiti core flow
- audit/material/invoice/purchase flow je blokiran
- postoji zabuna oko realnih podataka ili fiskalizacije

### Waived

Waiver je dopušten samo ako maintainer izričito prihvati rizik i u ADR-u napiše:

- zašto se tagira bez human pilota
- koji rizik se prihvaća
- kada će human pilot ipak biti napravljen
- zašto nema real patient data

## 9. v14 Codex Master Prompt

```text
You are a senior release maintainer and pilot execution assistant.

You are working on radicdavor/ASTRA-Clinic-Core.

ASTRA Clinic Core has completed v13. The current state is:

- maintainer command-level dry-run passed
- human pilot is still pending
- ADR 0001 is Deferred
- v0.1-pilot tag is blocked until human pilot is completed or formally waived
- real patient data is forbidden
- real Croatian fiscalization is not implemented
- no P0/P1 are known from command-level validation
- one P2 process issue remains: no human participant feedback yet

The next sprint is not a feature sprint.

The next sprint is:

Human Pilot Execution Gate

Main goal:
Either complete the human pilot and update all evidence files, or keep the project explicitly deferred. Do not add product features.

Non-negotiable rules:
- Do not add new features.
- Do not add new integrations.
- Do not add clinical modules.
- Do not add AI automations.
- Do not tag v0.1-pilot unless the evidence gate passes or maintainer waiver is explicitly documented.
- Do not enable real patient data.
- Do not imply real fiscalization.

Phase 1 — If human pilot has been run, update the report

Update:

docs/pilot_sessions/2026-07-05_human_pilot_01.md

Only update it with actual pilot results. Do not fabricate.

Required fields:
- Status: Completed / Deferred / Waived
- Date/time
- Facilitator
- Participant role
- Browser/device
- Commit SHA
- Task completion table
- Observed friction
- Findings table
- Real-data confusion yes/no
- Fiscalization confusion yes/no
- Go/No-Go recommendation

If the human pilot has not been run, keep it pending and state that no feature work should proceed.

Phase 2 — Update human pilot triage

Update:

docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md

Every finding must have:
- ID
- severity
- area
- summary
- owner
- status
- release decision impact
- GitHub issue link or to-create

If no actual pilot was run, keep HP01-001 open as P2 process debt.

Phase 3 — Update Go/No-Go matrix

Update:

docs/V0_1_GO_NO_GO_MATRIX.md

Human pilot row must be one of:
- Completed — Go candidate
- Pending — Deferred
- Waived — Go candidate with risk explicitly documented

Update audit/material/invoice/purchase rows from actual pilot evidence.

Phase 4 — Update ADR 0001

Update:

docs/ADR/0001-v0-1-pilot-decision.md

Set status:
- Accepted only if human pilot completed and no P0/P1 remain
- Deferred if human pilot pending or P0/P1 exist
- Waived only if maintainer explicitly accepts risk

Phase 5 — Update release notes

Update:

docs/releases/V0_1_PILOT_RELEASE_NOTES.md

Only mark QA/human pilot as passed if evidence exists.

If still pending, explicitly say:
- Human pilot pending
- v0.1-pilot tag deferred

Phase 6 — If accepted, prepare tag checklist

If Accepted, update:

docs/V0_1_PILOT_RELEASE_CHECKLIST.md

Mark checklist items as ready only if verified.

Do not tag from Codex unless explicitly requested by maintainer.

Phase 7 — If deferred, create next-action report

If Deferred, create:

docs/NEXT_ACTION_BEFORE_V0_1_TAG.md

Include:
- what blocks tag
- owner
- exact next human action
- expected evidence file
- what not to build yet

Suggested commit sequence:
1. docs: update human pilot evidence status
2. docs: update human pilot triage
3. docs: update go no-go matrix
4. docs: update pilot ADR decision
5. docs: update v0.1 release notes evidence
6. docs: update pilot release checklist if accepted
7. docs: add next action before v0.1 tag if deferred

Definition of done:
- evidence status is truthful
- no fabricated pilot results
- ADR status matches evidence
- release notes match evidence
- tag decision is explicit
- no feature scope was added
- real-data block remains intact
```

## 10. Ako nema human pilota — što napraviti odmah

Ako human pilot još nije odrađen, jedini ispravan commit je dokumentacijski:

- zadržati ADR Deferred
- zadržati human pilot report pending
- zadržati tag blocked
- dodati `docs/NEXT_ACTION_BEFORE_V0_1_TAG.md`

To nije zastoj. To je zrela release disciplina.

## 11. Zaključak

Projekt sada ima dovoljno koda za demo. Nema dovoljno ljudskog feedbacka za alpha.

Sljedeći pravi korak je neugodan, ali nužan: dati aplikaciju čovjeku koji je nije gradio i gledati gdje zapinje.
