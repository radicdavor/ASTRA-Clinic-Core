# ASTRA Clinic Core — kritički osvrt v7

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Codex je implementirao velik dio v6 smjera. Projekt je sada znatno bliže stvarnom clinic-operations MVP-u nego ranije. Najveća promjena je da više nije samo backend-first: frontend sada ima ključne operativne workflowe.

Potvrđeno je da postoje:

- Dashboard workflow za završetak termina uz potrošnju materijala.
- Dashboard akcija za kreiranje nacrta računa iz termina.
- UI za zaprimanje narudžbenice po stavkama.
- UI za izdavanje računa, prikaz fiskalizacijskog statusa i evidentiranje uplata.
- UI za API key management.
- Release checklist.
- Manual QA checklist.
- Demo data policy.
- Changelog.
- Početni module manifest katalog.

Moj stav: **v6 je prvi sprint nakon kojeg ASTRA počinje izgledati operativno, a ne samo arhitektonski dobro.**

Ali još uvijek nije spremna za stvarne pacijente. Sljedeći korak mora biti **Pilot Readiness Sprint**: stabilizirati realni demo/pilot tok od početka do kraja, dodati e2e/smoke testove, završiti module loader i napraviti sigurnu pripremu za zatvoreni pilot s demo podacima.

## Što je dobro implementirano

### 1. Dashboard je postao operativni ekran

`frontend/src/pages/Dashboard.tsx` sada više nije samo prikaz dnevnog rasporeda. Ima:

- filtre po liječniku, sobi, usluzi i statusu
- operativna upozorenja za nisku zalihu i rokove
- brze statusne radnje
- akciju “Materijal”
- akciju “Račun”
- modal za završetak termina uz potrošnju materijala

To je velika promjena. Dnevni raspored sada postaje radni cockpit.

### 2. Potrošnja materijala kroz UI postoji

Dashboard poziva endpoint za suggested material consumption, prikazuje materijale, dopušta unos količina, traži potvrdu i poziva `complete-with-consumption`.

To zatvara najvažniji clinic workflow:

termin -> usluga -> potrošnja materijala -> status completed.

### 3. Purchase receiving UI postoji

`frontend/src/pages/PurchaseOrders.tsx` sada ima workflow za zaprimanje narudžbenice po stavkama:

- prikaz naručene količine
- prikaz zaprimljene količine
- prikaz preostale količine
- unos količine
- unos LOT-a
- unos roka trajanja
- izbor lokacije
- potvrda zaprimanja

To je ključni korak prema stvarnom inventory/procurement workflowu.

### 4. Invoice issue/payment UI postoji

`frontend/src/pages/Invoices.tsx` sada podržava:

- odabir računa
- dodavanje stavki dok je račun draft
- izdavanje računa
- prikaz fiskalizacijskog statusa, providera i poruke
- evidentiranje uplate

To zatvara workflow:

termin -> nacrt računa -> izdavanje -> uplata.

### 5. API key management UI postoji

`frontend/src/pages/ApiKeys.tsx` omogućuje:

- listu API ključeva
- kreiranje ključa
- izbor scopeova
- prikaz raw ključa samo jednom
- deaktivaciju ključa
- prikaz zadnje upotrebe

To je vrlo važno za AI agente i vanjske integracije.

### 6. Release disciplina je počela

Postoje:

- `CHANGELOG.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/MANUAL_QA_CHECKLIST.md`
- `docs/DEMO_DATA_POLICY.md`

To mijenja mentalitet projekta iz “kodiramo featuree” u “održavamo proizvod”. To je dobro.

## Preostali problemi

### 1. UI workflowi postoje, ali još nisu dovoljno zaštićeni od pogrešnog korištenja

UI sada ima osnovne workflowe, ali treba dodatna ergonomija i sigurnost:

- jasnije prikazati koji materijali su obavezni, opcionalni i varijabilni
- prikazati dostupnu zalihu prije potvrde
- blokirati potvrdu ako obavezni varijabilni materijal nema količinu
- jasnije prikazati backend error poruke
- kod zaprimanja narudžbenice unaprijed blokirati over-receive na frontendu
- kod izdavanja računa upozoriti ako nema stavki ili je total 0

Backend treba ostati izvor istine, ali UI mora sprječavati očite greške.

### 2. Appointments stranica je još samo lista

Dashboard je dobio materijalni workflow, ali `Appointments.tsx` je još samo lista termina. To nije nužno problem, ali dugoročno treba appointment detail page.

Appointment detail bi trebao imati:

- podaci pacijenta
- termin/status
- usluga
- materijalni workflow
- link/nacrt računa
- audit timeline
- napomene

### 3. Module manifest postoji, ali loader nije vidljiv

Postoji `backend/app/modules/catalog/gastroenterology/module.json` i `services.json`, ali nisam vidio stvarni loader servis. `Modules.tsx` je još samo tablica modula iz API-ja.

Potrebno:

- data-only manifest loader
- idempotent import services/material templates
- API za pregled manifest modula
- testovi loadera

Bez toga modularnost ostaje katalog, a ne mehanizam.

### 4. PostgreSQL integration test coverage treba dalje potvrditi

V5 je dodao `pg_db` i CI `TEST_DATABASE_URL`; v6 je trebao dodatno pojačati PostgreSQL coverage. Treba jasno dokumentirati koji testovi su SQLite unit, a koji su PostgreSQL integration.

Ako se to ne vidi iz strukture direktorija, treba dodati jasnu strukturu:

- `backend/tests/unit/`
- `backend/tests/integration/`

ili markere:

- `@pytest.mark.integration`
- `@pytest.mark.postgres`

### 5. Nema end-to-end smoke testa za demo flow

Sada kad backend i frontend imaju workflowe, treba jedan e2e smoke flow:

1. login
2. create/choose appointment
3. complete appointment with material consumption
4. verify stock movement
5. create draft invoice
6. issue invoice
7. record payment
8. receive purchase order
9. verify inventory changed

To može biti Playwright ili API-level smoke test. Bez toga ne znamo radi li cijeli lanac.

### 6. API key UI dopušta samo mali fixed scope set

`ApiKeys.tsx` ima `commonScopes`, ali za admin bi bolje bilo povući dostupne scopeove iz backend konfiguracije ili barem uključiti sve relevantne AI-safe scopeove.

Također treba bolje odvojiti:

- AI-safe scopeovi
- read-only scopeovi
- dangerous scopeovi

### 7. Fiskalizacijski prikaz postoji, ali workflow mora jasno reći da je Noop/stub

Invoices UI prikazuje fiscalization status/provider/message, što je dobro. Ali korisnik mora jasno znati da Noop/stub nije stvarna fiskalizacija.

Za demo je to dobro. Za produkciju mora biti nemoguće zamijeniti Noop za stvarnu fiskalizaciju.

## Ocjena nakon v6

### Backend

Dovoljno dobar za zatvoreni demo i interni pilot s demo podacima.

### Frontend

Sada napokon operativan za tri ključna procesa, ali treba refinement.

### Testovi/CI

Dobar baseline; treba jasnije razdvojiti unit/integration/e2e.

### Sigurnost

Napreduje, ali AI scope UX treba oprez.

### Modularnost

Početak postoji, ali loader još treba napraviti.

### Produktna zrelost

Projekt je blizu “demo-ready”, ali ne “production-ready”.

## Preporučeni sljedeći sprint

Naziv:

**Pilot Readiness Sprint**

Cilj:

Pripremiti ASTRA Clinic Core za zatvoreni demo/pilot s demo podacima, bez stvarnih pacijenata.

Prioriteti:

1. E2E demo smoke test
2. Appointment detail page
3. UI refinement za material consumption
4. UI refinement za purchase receiving
5. UI refinement za invoice issue/payment
6. API key scope UX hardening
7. Module manifest loader
8. Demo data reset command
9. Seeded demo scenario
10. Pilot runbook

## Zaključak

V6 je velik korak. Sada ASTRA više nije samo “dobar backend”. Ima prve radne tokove koji liječniku/recepciji/skladištu mogu imati smisla.

Moj čvrst stav: **sljedeći korak nije dodavati više medicine, nego napraviti jedan savršen demo/pilot flow**. Kad taj flow radi glatko od termina do potrošnje materijala, zaprimanja robe, računa i uplate, tek tada ima smisla širiti module i AI automatizacije.
