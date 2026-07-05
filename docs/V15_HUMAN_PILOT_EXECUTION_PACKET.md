# ASTRA Clinic Core — v15 Human Pilot Execution Packet

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Zašto ovaj dokument postoji

V14 je ispravno zaključao stanje: `v0.1-pilot` se ne smije tagirati dok human pilot nije dovršen ili dok maintainer eksplicitno ne napravi waiver.

Sada je potreban jedan praktičan, operativan paket koji kaže **što točno napraviti u stvarnoj pilot sesiji**, kako zabilježiti nalaze i kako donijeti odluku.

Ovaj dokument nije još jedan feature prompt. Ovo je execution packet.

## 2. Trenutni status

### Spremno

- Demo environment može se pokrenuti.
- Demo seed/reset postoji.
- Public config postoji.
- Demo banner postoji.
- Core pilot flow postoji.
- Facilitator sheet postoji.
- Human pilot report template postoji.
- Human pilot placeholder postoji.
- Go/No-Go matrix postoji.
- ADR 0001 postoji i status je `Deferred`.
- `NEXT_ACTION_BEFORE_V0_1_TAG.md` postoji.

### Nije spremno

- `v0.1-pilot` tag.
- Alpha planning.
- Real patient data.
- Real Croatian fiscalization.
- Broad clinical module expansion.
- AI receptionist or new AI mutation flows.

## 3. Jedina ispravna sljedeća aktivnost

Odraditi **human pilot session** s demo podacima.

Minimalni sudionik:

- jedna osoba koja nije razvijala aplikaciju
- idealno netko iz clinic workflowa: recepcija, sestra, liječnik, administracija, billing ili inventory

Ako nema takve osobe, može se napraviti maintainer-observed pilot, ali ga treba jasno označiti kao slabiji dokaz.

## 4. Pre-session checklist

Prije pilot sesije:

```bash
git pull
git log -1 --oneline
```

Pokrenuti demo:

```bash
docker compose down -v
docker compose up --build
```

Seed demo data:

```bash
docker compose exec backend python -m app.demo.seed
```

Provjeriti backend:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/public-config
```

`/api/public-config` mora jasno pokazati:

```json
{
  "real_data_allowed": false
}
```

Provjeriti frontend:

```text
http://localhost:5173
```

Mora biti vidljiv demo/development banner.

Otvoriti za vrijeme sesije:

- `docs/pilot_sessions/HUMAN_PILOT_FACILITATOR_SHEET.md`
- `docs/pilot_sessions/HUMAN_PILOT_REPORT_TEMPLATE.md`
- `docs/V0_1_GO_NO_GO_MATRIX.md`
- `.github/ISSUE_TEMPLATE/pilot_feedback.yml`

## 5. Pilot script za sudionika

Facilitator treba sudioniku dati zadatak, ne upute klik-po-klik.

### Zadatak 1 — Login i dashboard

Recite sudioniku:

> Prijavite se demo korisnikom i pronađite današnji raspored.

Promatrati:

- vidi li demo banner
- razumije li da su podaci demo
- zna li gdje je današnji raspored

### Zadatak 2 — Appointment detail

> Otvorite demo termin i pogledajte podatke o pacijentu, usluzi, liječniku i sobi.

Promatrati:

- nalazi li appointment detail bez pomoći
- razumije li status termina
- vidi li audit/stock/invoice dijelove

### Zadatak 3 — Status flow

> Promijenite status termina kao da je pacijent stigao i pregled je u tijeku.

Promatrati:

- jesu li statusi razumljivi
- je li korisnik zabrinut da radi nepovratnu akciju

### Zadatak 4 — Material consumption

> Završite termin uz potrošnju materijala.

Promatrati:

- razumije li što će se skinuti sa zalihe
- razumije li obavezno/opcionalno/varijabilno
- vidi li dostupnu zalihu
- razumije li potvrdu
- može li provjeriti stock movement nakon završetka

### Zadatak 5 — Invoice

> Kreirajte nacrt računa iz termina, izdajte račun i evidentirajte uplatu.

Promatrati:

- zna li gdje se račun nalazi
- razumije li draft vs issued
- razumije li payment status
- vidi li warning da fiskalizacija nije stvarna
- može li objasniti preostali iznos

### Zadatak 6 — Purchase receiving

> Zaprimite jednu stavku narudžbenice i provjerite da se zaliha promijenila.

Promatrati:

- razumije li naručeno / zaprimljeno / preostalo
- zna li odabrati lokaciju
- razumije li LOT/rok ako se pojave
- razumije li posljedicu zaprimanja

### Zadatak 7 — Audit

> Pronađite gdje se vidi što je napravljeno i tko je napravio promjenu.

Promatrati:

- nalazi li audit timeline/log
- razumije li tko/što/kada
- je li audit prikaz dovoljno čitljiv

## 6. Pravilo tišine za facilitatora

Facilitator ne smije pomagati odmah.

Preporuka:

- čekati 30 sekundi ako korisnik zastane
- prvo pitati: “Što biste očekivali da trebate kliknuti?”
- tek onda pomoći ako je korisnik blokiran

Ako korisnik zapne, to je nalaz.

Nemoj popravljati pilot usmenim objašnjenjem. Zapiši gdje je UI zakazao.

## 7. Evidence capture

Tijekom ili odmah nakon sesije ispuniti:

`docs/pilot_sessions/2026-07-05_human_pilot_01.md`

Obavezno zabilježiti:

- tko je sudionik po ulozi, bez osobnih podataka ako nije potrebno
- browser/device
- commit SHA
- task completion
- friction
- real-data confusion yes/no
- fiscalization confusion yes/no
- severity svakog nalaza
- Go/No-Go recommendation

Zatim ažurirati:

`docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md`

## 8. Kako klasificirati nalaze

### P0 — odmah blokira release

- real data uneseni ili skoro uneseni zbog nejasnog UI-ja
- participant misli da je fiskalizacija stvarna
- stock se krivo promijeni
- payment/invoice status krivo završi
- API key/permission bypass
- demo reset bi mogao dirati produkciju
- sustav se ruši u core flowu bez oporavka

### P1 — blokira release

- participant ne može dovršiti core flow
- appointment detail ne radi
- material consumption ne radi s validnom zalihom
- invoice issue/payment ne radi s validnim podacima
- purchase receiving ne radi s validnom stavkom
- audit nije dostupan za core flow

### P2 — može se deferati uz release note

- label je zbunjujući
- korisnik treba previše klikova
- warning je nejasan, ali postoji
- error message je loš, ali workaround postoji

### P3 — polish

- layout
- typo
- spacing
- manja jezična dorada

## 9. Go/No-Go pravilo

### Go za tag `v0.1-pilot`

Samo ako:

- human pilot completed
- nema P0/P1
- P2/P3 su triagirani
- demo banner vidljiv
- real-data confusion = No
- fiscalization confusion = No
- material/inventory workflow completed
- invoice/payment workflow completed
- purchase receiving completed
- audit trail reviewed
- ADR updated to Accepted
- release notes updated

### No-Go / Deferred

Ako:

- human pilot nije odrađen
- P0/P1 postoji
- korisnik ne razumije demo/real-data granicu
- korisnik misli da je fiskalizacija stvarna
- core flow se ne može dovršiti
- audit/material/invoice/purchase flow je blokiran

### Waiver

Ako maintainer želi tag bez human pilota, mora eksplicitno ažurirati:

- ADR 0001
- release notes
- Go/No-Go matrix

Waiver mora reći:

- što se waivea
- zašto
- koji rizik se prihvaća
- kada će se human pilot ipak napraviti

## 10. V15 Codex Master Prompt

```text
You are a senior pilot facilitator, release manager and QA triage assistant.

You are working on radicdavor/ASTRA-Clinic-Core.

The project has completed v14. The current state is:

- v0.1-pilot tag is blocked
- human pilot is pending unless updated by maintainer
- ADR 0001 is Deferred
- real patient data is forbidden
- real Croatian fiscalization is not implemented
- no broad new features should be added

The next sprint is:

Human Pilot Result Triage Sprint

Main goal:
Update the repository based on the actual human pilot result. If the pilot was not run, keep the release deferred and do not add features.

Non-negotiable rules:
- Do not fabricate pilot results.
- Do not add product features.
- Do not add integrations.
- Do not expand clinical modules.
- Do not add AI automations.
- Keep real-data block intact.
- Keep noop/stub fiscalization warning intact.

Phase 1 — Inspect human pilot status

Read:

docs/pilot_sessions/2026-07-05_human_pilot_01.md

docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md

docs/V0_1_GO_NO_GO_MATRIX.md

docs/ADR/0001-v0-1-pilot-decision.md

Determine whether status is:
- Completed
- Pending
- Waived
- Deferred

Phase 2 — If completed, normalize evidence

If human pilot was completed, ensure report includes:
- participant role
- browser/device
- commit SHA
- task completion table
- friction notes
- severity findings
- real-data confusion yes/no
- fiscalization confusion yes/no
- Go/No-Go

If any field is missing, add a TODO and keep release Deferred.

Phase 3 — If pending, create explicit no-feature next action

If still pending, update or create:

docs/NEXT_ACTION_BEFORE_V0_1_TAG.md

Keep it clear that the only next action is to run human pilot.

Phase 4 — Update issue triage

Every finding must have:
- ID
- severity
- area
- summary
- owner
- status
- release impact
- issue link or to-create

If no human pilot happened, preserve HP01-001 as open P2 process debt.

Phase 5 — Update Go/No-Go matrix

Set rows based on evidence:
- Human pilot
- Audit visibility
- Material workflow
- Invoice/payment workflow
- Purchase receiving workflow
- Real-data warning
- Fiscalization warning

Phase 6 — Update ADR

ADR status must be one of:
- Accepted
- Deferred
- Waived

Accepted only if human pilot completed and no P0/P1 remain.
Deferred if pending or P0/P1 exist.
Waived only if maintainer explicitly accepts risk.

Phase 7 — Update release notes

Update:

docs/releases/V0_1_PILOT_RELEASE_NOTES.md

Reflect:
- human pilot status
- P0/P1 status
- known limitations
- real-data status
- fiscalization status

Phase 8 — If Accepted, prepare tag readiness note

If Accepted, create:

docs/V0_1_TAG_READY.md

Include:
- evidence summary
- final checks
- tag command
- rollback command

Do not create tag automatically unless explicitly requested.

Phase 9 — If Deferred, keep next-action file current

If Deferred, ensure:

docs/NEXT_ACTION_BEFORE_V0_1_TAG.md

lists exact blocker and next human action.

Suggested commit sequence:
1. docs: inspect and update human pilot status
2. docs: update human pilot triage
3. docs: update go no-go matrix from evidence
4. docs: update pilot ADR status
5. docs: update v0.1 release notes status
6. docs: add tag readiness note if accepted
7. docs: keep next action before tag if deferred

Definition of done:
- repository truthfully reflects human pilot state
- no pilot result is fabricated
- release decision is clear
- P0/P1 policy is enforced
- no feature scope is added
- real-data block remains intact
```

## 11. Što sada NE raditi

Ne tražiti od Codexa:

- “dodaj još jedan modul”
- “dodaj AI recepcionara”
- “integriraj Google Calendar”
- “napravi OpenEMR integraciju”
- “dodaj stvarnu fiskalizaciju”
- “proširi sve protokole”

Dok human pilot nije završen, sve to je prerano.

## 12. Zaključak

Ovo je točka na kojoj projekt treba ljudsku stvarnost.

Ako human pilot prođe, `v0.1-pilot` tag ima smisla.

Ako ne prođe, najbolji sljedeći sprint je mali, fokusiran P0/P1 fix sprint.

U oba slučaja, odgovor mora doći iz pilot evidencea, ne iz još jedne pretpostavke.
