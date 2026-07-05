# ASTRA Clinic Core — kritički osvrt v9

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Codex je implementirao većinu v8 smjera. Projekt je sada vrlo blizu kontroliranog demo/pilot okruženja s demo podacima. Najvažnije: sada postoji jasna razlika između demo readiness i real-data readiness, što je presudno za zdravstveni softver.

Potvrđeno je da postoje:

- Pilot feedback template.
- Real data readiness checklist.
- Prošireni pilot runbook.
- Demo/development banner u AppShellu.
- Frontend pilot smoke script.
- Poboljšan invoice issue/payment UI.
- Poboljšan purchase receiving UI.
- Poboljšan API key scope UI.
- API key scope katalog na frontend strani.
- Appointment detail i audit timeline iz v7.
- Data-only module loader iz v7.

Moj stav: **ASTRA je sada demo/pilot-ready s demo podacima. Još nije production-ready i nije spremna za realne pacijente.**

Sljedeći sprint treba biti **Closed Pilot Execution Sprint**: ne graditi puno novih funkcija, nego provesti pilot disciplinirano, prikupiti feedback, zatvoriti blocker bugove i definirati minimalni “v0.1 pilot release”.

## Što je dobro nakon v8

### 1. Pilot feedback template postoji

`docs/PILOT_FEEDBACK_TEMPLATE.md` daje strukturirani način za prikupljanje povratnih informacija:

- uloga sudionika
- scenarij
- browser/device
- task outcome
- što je jasno
- što je zbunjujuće
- gdje je korisnik zapeo
- severity tablica
- odluka za sljedeći pilot

To je odličan korak jer se pilot više neće svesti na subjektivni dojam.

### 2. Real data readiness checklist jasno blokira realne pacijente

`docs/REAL_DATA_READINESS_CHECKLIST.md` jasno kaže da ASTRA nije spremna za stvarne pacijente dok se ne odrade security, GDPR/DPIA, backup, audit, fiscalization, hosting i operational kontrole.

To je vrlo važno. Demo readiness nije isto što i production readiness.

### 3. Pilot runbook je konkretniji

`docs/PILOT_RUNBOOK.md` sada ima:

- demo start
- demo login podatke
- reset demo data
- preporučeno trajanje
- role/personas
- 20-step demo script
- expected outcomes
- limitations
- fallback
- backup reminder

To je dovoljno da netko drugi može voditi demonstraciju.

### 4. Demo banner postoji

`AppShell.tsx` prikazuje banner za demo/development mode: “ne unositi stvarne podatke pacijenata”. To je jako dobro i mora ostati dok god projekt nije real-data ready.

### 5. Frontend smoke test postoji

`frontend/scripts/pilot-smoke.mjs` provjerava postojanje ključnih frontend artefakata i fraza:

- Dashboard
- AppointmentDetail
- PurchaseOrders
- Invoices
- ApiKeys
- AppShell
- AuditTimeline
- route `/appointments/:id`
- route `/api-keys`
- demo banner
- demo fiscalization warning
- before_json u audit timelineu

To nije puni Playwright e2e, ali je dobar lightweight guard.

### 6. Invoice UI je sigurniji

`Invoices.tsx` sada računa paid/remaining, blokira uplatu na draft/cancelled računima, blokira overpayment, traži potvrdu prije izdavanja računa, prikazuje fiscalization provider/status/message i eksplicitno upozorava da Noop fiskalizacija nije stvarna.

To je veliki korak u odnosu na raniju verziju.

### 7. Purchase receiving UI je sigurniji

`PurchaseOrders.tsx` sada validira:

- barem jedna količina
- over-receive
- lokacija
- LOT ako item traži lot tracking
- expiration ako item traži expiration tracking
- potvrda prije zaprimanja

To je ispravno za demo/pilot.

### 8. API key UX je bolji

`ApiKeys.tsx` sada povlači scope katalog, grupira scopeove po kategorijama, traži dodatnu potvrdu za dangerous scopes, ima copy-to-clipboard i potvrdu za deaktivaciju.

To je jako važno za AI agente i vanjske integracije.

## Preostale slabosti

### 1. Module loader još treba testove

Nisam našao jasan `test_module_manifest_loader.py` ili sličan test. Loader je potencijalno važan jer će kasnije unositi servise i material templates. Mora biti testiran prije širenja modula.

Minimalno testirati:

- load module once
- load same module twice without duplicates
- update existing service by code
- material template import by service code + item SKU
- missing item skip behavior
- invalid manifest validation error

### 2. Frontend smoke je statički, ne pravi user-flow test

`pilot-smoke.mjs` je koristan, ali samo čita datoteke i traži stringove. To ne dokazuje da korisnik može kliknuti kroz demo.

Sljedeći korak:

- dodati Playwright minimal e2e ili
- backend API e2e + frontend static smoke ostaviti kao privremenu mjeru, ali jasno dokumentirati da nije pravi UI test.

### 3. Demo banner ovisi o frontend env varijabli

`showDemoBanner = import.meta.env.VITE_APP_ENV !== "production"`. To je dobro, ali frontend env se može krivo buildati. Dugoročno bi bilo bolje da backend izloži `/api/config/public` s `app_env`, `demo_mode`, `real_data_allowed=false`, pa frontend prikazuje banner prema backend truthu.

### 4. Real data readiness je dokument, ne enforcement

Checklist postoji, ali sustav još nema enforceani “real data lock”. To je prihvatljivo za demo, ali prije ikakvog real-data pilotiranja treba backend guard:

- DEMO_MODE true/false
- REAL_DATA_ALLOWED false by default
- banner + API warning
- optional hard block za demo accounts u production

### 5. Pilot feedback nije povezan s issue workflowom

Template postoji, ali trebalo bi dodati GitHub issue template ili folder za pilot session notes. Inače će feedback ostati u dokumentu koji se ne koristi disciplinirano.

### 6. Audit timeline može biti još bolji

AuditTimeline je dobar početak, ali za korisnike treba prikazati:

- “tko” razumljivije
- prije/poslije diff čitljivije
- akcije human labelima
- filter po action

### 7. Nije još vrijeme za širenje medicinskih modula

Iako postoji module loader, još ne treba širiti Gastro/Endoscopy/Dermato module agresivno. Prvo treba odraditi kontrolirani pilot i vidjeti je li core flow stvarno razumljiv korisnicima.

## Ocjena nakon v8

### Demo readiness

Da, s demo podacima.

### Pilot readiness

Da, za zatvoreni interni pilot s demo/anonymized podacima i jasnim ograničenjima.

### Real patient readiness

Ne.

### Frontend operativnost

Značajno bolja.

### Test coverage

Dobra za backend; frontend e2e još slab.

### Modul loader

Postoji, ali treba testove.

### Sigurnost

Dobra za demo, još nije dovoljna za stvarne pacijente.

## Preporučeni sljedeći sprint

Naziv:

**Closed Pilot Execution Sprint**

Cilj:

Izvesti kontrolirani pilot s demo podacima, prikupiti feedback, popraviti blockers i pripremiti v0.1 pilot release.

Prioriteti:

1. Testirati module loader.
2. Dodati pravi minimalni frontend e2e ili dokumentirano odgoditi.
3. Dodati GitHub issue template za pilot feedback.
4. Dodati backend public config endpoint za demo/real-data flags.
5. Dodati real-data guard/detection za demo accounts.
6. Izvesti jedan pilot session prema runbooku.
7. Pretvoriti feedback u issues.
8. Popraviti P0/P1 bugove.
9. Napraviti v0.1 pilot release checklist.
10. Tek nakon toga planirati Gastro module v1.

## Zaključak

V8 je dobro odrađen. ASTRA je sada dovoljno zrela za demonstraciju kontroliranog workflowa.

Moj čvrst stav: **sada prestati pisati nove velike funkcije i prvi put stvarno koristiti aplikaciju prema runbooku.** Pilot feedback će reći više nego još 10 promptova. Sljedeći razvoj treba biti vođen stvarnim ponašanjem korisnika u demo/pilot flowu.
