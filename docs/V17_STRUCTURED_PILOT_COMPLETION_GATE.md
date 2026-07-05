# ASTRA Clinic Core — v17 Structured Pilot Completion Gate

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Zašto ovaj dokument postoji

V16 je donio važan pomak: korisnik/maintainer je neformalno prošao kroz program i javio: **“Za sada dobro.”**

To je vrijedna human signal informacija, ali još nije dovoljno za formalni `v0.1-pilot` tag.

Razlog: neformalni walkthrough nema još sve strukturirane elemente koje smo sami definirali kao uvjet za release decision:

- task-by-task completion table
- role / participant context
- browser/device evidence
- observed friction
- real-data confusion check
- fiscalization confusion check
- audit/material/invoice/purchase workflow confirmation
- formal Go/No-Go matrix update
- ADR transition iz `Deferred` u `Accepted`, `Deferred` ili `Waived`

Ovaj dokument služi kao most između:

- **neformalnog pozitivnog dojma** i
- **formalnog pilot release evidencea**.

Moj stav: sada ne treba dodavati funkcije. Treba formalizirati već odrađeni prolaz.

## 2. Trenutni status nakon V16

Canonical evidence:

- `docs/pilot_sessions/2026-07-05_human_pilot_01.md`
- `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`
- `docs/NEXT_ACTION_BEFORE_V0_1_TAG.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `docs/ADR/0001-v0-1-pilot-decision.md`

Current known state:

- Informal human walkthrough: completed
- User/maintainer reported: “Za sada dobro”
- Known P0: none reported
- Known P1: none reported
- Known P2: structured report incomplete
- Human pilot evidence: partial, not formal
- ADR: still should remain Deferred until formal evidence or waiver
- `v0.1-pilot` tag: still blocked unless structured evidence is completed or maintainer explicitly waives the missing fields
- Real patient data: forbidden
- Real Croatian fiscalization: not implemented
- Broad feature work: still paused

## 3. Kako tretirati “Za sada dobro”

To je pozitivan signal, ali ne i release evidence.

Može se koristiti kao:

- signal da nema očitog showstoppera
- razlog da nastavimo prema formalizaciji pilota
- osnova za “Go for continued closed pilot usage with demo data”

Ne može se koristiti kao:

- dokaz da workflow razumije ne-developer korisnik
- dokaz da nema P0/P1
- dokaz da je audit/fiskalizacija/material flow korisniku jasan
- osnova za real patient data
- osnova za realnu fiskalizaciju
- osnova za širenje modula

## 4. Što sada treba formalno popuniti

U dokumentu:

`docs/pilot_sessions/2026-07-05_human_pilot_01.md`

potrebno je popuniti ili eksplicitno waiveati sljedeće:

### 4.1 Session metadata

- stvarni browser/device
- je li korisnik bio developer/maintainer ili netko iz klinike
- je li pilot bio samostalan ili vođen
- je li korišten demo seed
- commit SHA pri izvođenju

### 4.2 Task completion table

Za svaki zadatak upisati:

| Task | Completed | Notes |
| --- | --- | --- |
| Login | Yes/No | |
| Find today's schedule | Yes/No | |
| Open appointment detail | Yes/No | |
| Update appointment status | Yes/No | |
| Review material suggestion | Yes/No | |
| Complete with material consumption | Yes/No | |
| Verify stock movement | Yes/No | |
| Create draft invoice | Yes/No | |
| Issue invoice | Yes/No | |
| Record payment | Yes/No | |
| Receive purchase order | Yes/No | |
| Review audit trail | Yes/No | |

### 4.3 Confusion checks

Obavezno označiti:

- Real-data confusion observed: Yes/No
- Fiscalization confusion observed: Yes/No
- Did user understand demo banner: Yes/No
- Did user understand noop/stub fiscalization: Yes/No
- Did user understand material consumption affects inventory: Yes/No

### 4.4 Findings

Ako nema nalaza, eksplicitno napisati:

- P0: none observed
- P1: none observed
- P2: list or none
- P3: list or none

Ako postoje nalazi, svaki mora imati:

- severity
- area
- summary
- release impact
- issue link ili `to-create`

### 4.5 Go/No-Go recommendation

Jedno od:

- Go for v0.1-pilot tag
- Go for continued demo pilot only, tag deferred
- No-Go until P0/P1 fixed
- Waived by maintainer with explicit risk

## 5. Formal decision options

### Option A — Accepted

Dopušteno samo ako:

- pilot evidence je strukturirano popunjen
- nema P0/P1
- confusion checks su negativni za real-data i fiscalization confusion
- core flow je dovršen
- ADR se ažurira na Accepted
- release notes se ažuriraju
- release checklist se označi prema dokazima

### Option B — Deferred

Koristiti ako:

- task table nije popunjen
- confusion checks nisu popunjeni
- browser/device/role nisu jasni
- postoji P0/P1
- maintainer ne želi waiveati manjak formalnih podataka

### Option C — Waived

Koristiti samo ako maintainer kaže:

> Prihvaćam da je pilot neformalan i svejedno želim tagirati `v0.1-pilot` uz jasno dokumentiran rizik.

Tada se mora ažurirati:

- ADR
- release notes
- Go/No-Go matrix
- tag checklist

Waiver ne dopušta real patient data.

## 6. Što se smije raditi prije formalizacije

Dopušteno:

- popuniti pilot report
- popuniti triage
- ažurirati ADR
- ažurirati release notes
- ažurirati Go/No-Go matrix
- napraviti issue payloads
- popraviti P0/P1 ako se pronađu

Nije dopušteno:

- novi featurei
- novi moduli
- real patient data
- real fiskalizacija
- AI receptionist
- Google Calendar/OpenEMR integracije
- broad UI redesign
- alpha planning bez evidencea

## 7. Minimalni “formalization interview” ako se pilot već dogodio

Ako je korisnik već prošao program, a nije popunjena tablica, može se retroaktivno napraviti kratki interview od 10 minuta.

Pitanja:

1. Jeste li se mogli prijaviti bez pomoći?
2. Jeste li našli današnji raspored?
3. Jeste li otvorili appointment detail?
4. Jeste li promijenili status termina?
5. Jeste li završili termin s potrošnjom materijala?
6. Jeste li vidjeli da se zaliha promijenila?
7. Jeste li kreirali i izdali račun?
8. Jeste li evidentirali uplatu?
9. Jeste li zaprimili narudžbenicu?
10. Jeste li našli audit trail?
11. Jeste li u bilo kojem trenutku mislili da smijete unositi stvarne pacijente?
12. Jeste li u bilo kojem trenutku mislili da je fiskalizacija stvarna?
13. Što je bilo nejasno?
14. Što je bilo opasno ili zbunjujuće?
15. Što biste promijenili prije da to pokažemo drugoj osobi?

Odgovori se zatim unesu u pilot report.

## 8. Release impact

Ako retroaktivni interview potvrdi:

- svi core taskovi su dovršeni
- nema real-data confusion
- nema fiscalization confusion
- nema P0/P1

onda se može razmotriti `v0.1-pilot` tag.

Ako ne potvrdi, release ostaje Deferred.

## 9. v17 Codex Master Prompt

```text
You are a senior release governance assistant and pilot evidence normalizer.

You are working on radicdavor/ASTRA-Clinic-Core.

The project has completed v16.

Current evidence state:
- informal human walkthrough has been reported
- user/maintainer said: “Za sada dobro”
- no P0/P1 have been reported
- structured pilot report is incomplete
- ADR remains Deferred unless structured evidence or waiver is provided
- v0.1-pilot tag remains blocked unless formal evidence is completed or explicitly waived
- real patient data remains forbidden
- real Croatian fiscalization is not implemented

This is not a feature sprint.

This is a Structured Pilot Completion Gate.

Non-negotiable rules:
- Do not add features.
- Do not add modules.
- Do not add integrations.
- Do not add AI automations.
- Do not fabricate pilot results.
- Do not enable real patient data.
- Do not imply real fiscalization.

Phase 1 — Inspect pilot report

Read:

docs/pilot_sessions/2026-07-05_human_pilot_01.md

docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md

docs/V0_1_GO_NO_GO_MATRIX.md

docs/ADR/0001-v0-1-pilot-decision.md

docs/releases/V0_1_PILOT_RELEASE_NOTES.md

Determine whether report is:
- Informal only
- Structured complete
- Waived
- Deferred

Phase 2 — If structured answers are provided by maintainer

Update `docs/pilot_sessions/2026-07-05_human_pilot_01.md` with actual answers only.

Required updates:
- status
- participant context
- browser/device
- task completion table
- observed friction
- confusion checks
- findings severity
- Go/No-Go recommendation

Do not infer answers not provided.

Phase 3 — If report remains informal

Keep status as informal / incomplete.

Update:

docs/NEXT_ACTION_BEFORE_V0_1_TAG.md

with exact missing fields.

Keep ADR Deferred.

Phase 4 — Update triage

Update:

docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md

Include:
- missing structured evidence as P2 process item
- any actual findings as P0/P1/P2/P3

Phase 5 — Update Go/No-Go matrix

If structured complete and no P0/P1:
- mark human pilot as completed
- mark workflows according to evidence

If still incomplete:
- keep human pilot as incomplete/informal
- tag remains blocked

Phase 6 — Update ADR

ADR status rules:
- Accepted only with structured complete evidence and no P0/P1
- Deferred if incomplete or P0/P1 exists
- Waived only if maintainer explicitly accepts risk

Phase 7 — Update release notes

Reflect evidence truthfully:
- human pilot informal / completed / waived / deferred
- P0/P1 status
- P2/P3 status
- real-data status
- fiscalization status

Phase 8 — If Accepted, create tag readiness note

Only if Accepted:

Create:

docs/V0_1_TAG_READY.md

Include evidence summary, tag command and rollback command.

Phase 9 — If Deferred, update next action

If Deferred:

Update:

docs/NEXT_ACTION_BEFORE_V0_1_TAG.md

List missing fields precisely.

Suggested commit sequence:
1. docs: inspect structured pilot completion gate
2. docs: update human pilot report from provided evidence
3. docs: update pilot triage from evidence
4. docs: update go no-go matrix
5. docs: update ADR decision
6. docs: update release notes status
7. docs: add tag readiness if accepted
8. docs: update next action if deferred

Definition of done:
- repository truthfully reflects pilot evidence
- informal walkthrough is not overstated
- missing structured evidence is explicit
- no feature work is added
- tag decision remains blocked unless evidence supports it
- real-data block remains intact
```

## 10. Što ti sada trebaš napraviti, praktično

Odgovori na 15 pitanja iz sekcije 7.

Ne moraš pisati roman. Dovoljno je:

```text
1 Da
2 Da
3 Da
4 Da
5 Da
6 Da
7 Da
8 Da
9 Da
10 Da
11 Ne
12 Ne
13 Nejasno: ...
14 Opasno: ...
15 Prije drugog pilota promijeniti: ...
```

Na temelju toga se može formalizirati report.

## 11. Zaključak

“Za sada dobro” je dobar signal.

Sada ga treba pretvoriti u structured evidence.

Tek tada `v0.1-pilot` može prijeći iz ideje u odgovornu release odluku.
