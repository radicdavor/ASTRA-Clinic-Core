# ASTRA Clinic Core — kritički osvrt v4

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Repozitorij je sada u fazi ozbiljnog MVP-a. U odnosu na prethodne revizije, više nema smisla govoriti da je projekt samo ideja ili scaffold. Postoji konkretan backend model i poslovna logika za termine, inventar, nabavu, potrošnju materijala i račune.

Najvažniji zaključak ove revizije:

**ASTRA Clinic Core sada ima dobru domensku jezgru, ali nema dokaz pouzdanosti. Sljedeći rad mora biti testiranje, CI, transakcijska provjera i produkcijski hardening.**

Drugim riječima: sada je opasno dodavati još featurea prije nego što se uvedu testovi.

## Što je vidljivo u zadnjem stanju

### 1. README jasno postavlja sigurnosnu granicu

README ima eksplicitnu sigurnosnu napomenu: zadani korisnik, lozinka i Docker postavke su samo za razvoj; prije stvarne uporabe treba promijeniti admin lozinku, postaviti jak JWT secret, ograničiti CORS, koristiti HTTPS, podesiti backup PostgreSQL baze i napraviti GDPR/access-control provjeru. Također piše da ASTRA Clinic Core nije certificirani EMR ni certificirani medicinski uređaj.

To je dobro i nužno. Projekt bi bez te napomene mogao djelovati zrelije nego što jest.

### 2. Funkcionalni opseg je sada ambiciozan, ali smislen

README navodi:

- pacijente
- termine
- Alembic migracije
- permission-based RBAC
- strukturirani audit log
- validaciju konflikta termina
- scoped API key za AI agente
- inventar
- nabavu
- naplatu
- predloške potrošnje materijala
- automatsku FEFO potrošnju

To je dobar smjer. ASTRA je sada jasnije definirana kao clinic-operations platforma, ne kao puni EMR.

### 3. Inventory/procurement/billing rute su sada dosta zrelije

`backend/app/api/routes/inventory.py` koristi:

- `Actor`
- `require_permission`
- `response_model`
- `audit_actor`
- jasne permissione za inventory/procurement/billing
- validaciju LOT-a i roka trajanja
- audit prije/poslije promjena
- izdvojene servise za appointment materials, billing i procurement

To je veliki arhitektonski napredak.

### 4. Potrošnja materijala po terminu izdvojena je u servis

`backend/app/services/appointment_materials.py` je dobar iskorak jer odvaja domensku logiku od route filea.

Servis sada:

- čita `ServiceMaterialTemplate`
- validira obavezni varijabilni materijal
- zbraja tražene količine po artiklu
- provjerava dostupnost prije mutacije
- koristi FEFO potrošnju
- auditira promjene na inventory itemu i stock movementima

To je točan smjer.

### 5. Procurement receiving je stvarni workflow

`backend/app/services/procurement.py` validira stavke narudžbenice, sprječava over-receive, traži LOT/expiration kad artikl to zahtijeva, stvara `InventoryBatch`, stvara `StockMovement`, ažurira `quantity_received`, recalculira stock i derivira status narudžbenice.

To je sada pravi početak nabavnog modula, ne samo placeholder.

## Najveći problemi sada

### 1. Nema vidljivog test suitea

Pretraga po repozitoriju nije našla pytest/test/CI artefakte. Ovo je sada najveća rupa.

Bez testova ne smije se dalje širiti funkcionalnost.

Rizična područja bez testova:

- preklapanje termina
- RBAC i API key scopeovi
- FEFO potrošnja
- potrošnja materijala po terminu
- rollback kod nedovoljne zalihe
- zaprimanje više stavki narudžbenice
- over-receive
- izdavanje računa
- parcijalne uplate
- audit before/after

### 2. Nema vidljivog CI-ja

Ako nema GitHub Actions workflowa, Codex može lako napraviti regresiju u backendu ili frontendu bez da se to odmah vidi.

Minimalno treba:

- backend pytest
- frontend build
- Alembic migration smoke test
- Docker compose smoke test

### 3. Frontend vjerojatno ne prati backend mogućnosti

Backend sada ima više ozbiljne poslovne logike nego što prosječan UI obično prati u ovoj fazi.

Posebno treba provjeriti postoje li ekrani za:

- zaprimanje narudžbenice po stavkama
- partial receive
- otpis s razlogom
- transfer skladišta
- završetak termina s potvrdom potrošnje materijala
- izdavanje računa
- dodavanje uplata
- pregled audit loga s filtrima
- upravljanje API ključevima

Bez toga sustav ostaje tehnički jak, ali operativno nezgodan.

### 4. Nema fiskalizacijskog adaptera

Billing sada ima dobar MVP foundation, ali za Hrvatsku treba barem arhitektonski stub:

- `FiscalizationProvider`
- `NoopFiscalizationProvider`
- `CroatiaFiscalizationProviderStub`
- audit pokušaja fiskalizacije
- statusi: not_configured, pending, success, failed

Ne treba još raditi stvarnu fiskalizaciju, ali mora postojati čista granica.

### 5. GDPR je samo upozorenje, ne funkcionalnost

README dobro upozorava na GDPR/access-control, ali sustav treba stvarne alate:

- user management
- disable user
- token expiration
- access log za čitanje pacijentovih podataka
- export pacijentovih podataka
- soft delete/retention politika
- audit čitanja osjetljivih entiteta, barem opcionalno

### 6. OpenAPI treba postati ugovor, ne samo automatska dokumentacija

`response_model` se koristi u inventory rutama, ali treba sustavno proći sve rute.

Vanjski sustavi, AI agenti i budući integracijski partneri trebaju stabilan API contract:

- jasne request sheme
- jasne response sheme
- error response model
- examples
- zabrana curenja hashiranih ključeva, lozinki ili internih podataka

### 7. Transakcijska disciplina mora biti dokazana testovima

Neki servisi već validiraju unaprijed, što je dobro, ali sada treba dokazati rollback ponašanje:

- ako potrošnja materijala ne uspije, appointment ne smije završiti kao completed
- ako purchase receiving padne na jednoj stavci, prethodne stavke iz istog requesta ne smiju ostati zaprimljene
- ako uplata iznad iznosa padne, invoice status se ne smije promijeniti
- ako transfer padne, source batch mora ostati netaknut

### 8. Modularnost još nije pravi engine

Projekt ima `Module` i `Service`, ali za stvarnu modularnost treba manifest sustav:

- module.json
- services.json
- material_templates.json
- workflows.json
- patient_instructions.json
- ai_prompts.json

Moduli moraju biti podaci/konfiguracija, ne proizvoljan izvršni plugin kod.

## Moja ocjena

### Arhitektura

Vrlo dobra za ovaj stadij. Smjer je ispravan.

### Backend domena

Snažna MVP jezgra.

### Inventory/procurement

Najveća vrijednost projekta. Ovo već izgleda kao početak medicinskog ERP-light sustava.

### Billing

Dobar temelj, ali nije spreman za Hrvatsku bez fiskalizacijskog adaptera.

### AI integracija

Dobro zamišljena kroz scoped API key, ali AI agent ne smije dobiti više ovlasti dok testovi ne pokriju permissione.

### Testovi

Najveći blocker.

### Produkcija

Nije spremno za stvarnu uporabu.

## Preporučeni sljedeći Codex sprint

Naziv sprinta:

**Reliability First Sprint**

Prioriteti:

1. pytest infrastruktura
2. testovi za appointment overlap
3. testovi za RBAC i AI API key scope
4. testovi za FEFO i appointment material consumption
5. testovi za purchase receiving i rollback
6. testovi za invoice/payment workflow
7. audit tests
8. GitHub Actions CI
9. OpenAPI cleanup
10. fiscalization adapter stub
11. production hardening docs
12. tek onda frontend operational screens

## Zaključak

ASTRA Clinic Core sada ima dovoljno dobru jezgru da ga vrijedi ozbiljno graditi dalje.

Ali sada treba stati s dodavanjem novih funkcija. Sljedeći korak nije još jedan modul, još jedan AI feature ili ljepši dashboard. Sljedeći korak je dokazati da postojeće funkcije rade ispravno i da se neće raspasti kod prve promjene.

Moj stav: **bez testova i CI-ja ovaj projekt ne smije ići u širenje**. Nakon testova i CI-ja, ima potencijal postati jako zanimljiva open-source clinic operations platforma.
