# Kritički osvrt na ASTRA Clinic Core

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Projekt više nije samo prazan koncept. Već postoji funkcionalni početni kostur: Docker Compose, FastAPI backend, PostgreSQL, React/Vite frontend, osnovni auth, pacijenti, termini, usluge, audit log, AI rute, inventar, dobavljači, narudžbenice i računi.

To je jako dobar početak, ali trenutno je to još uvijek **MVP scaffold**, a ne produkcijski siguran clinic operating system.

Glavni problem nije smjer, nego dubina implementacije: modeli postoje, endpointi postoje, ali nedostaju stroge validacije, migracije, permission model, testovi, ozbiljna skladišna logika, fiskalizacijski sloj, pravi workflow engine i realna AI sigurnost.

## Što je dobro

### 1. Tehnološki stack je dobar

FastAPI + PostgreSQL + React/Vite + Docker Compose je razuman izbor. Nije pretežak, ali je dovoljno ozbiljan za lokalni rad i kasniju cloud migraciju.

### 2. Core domenski model je dobro pogođen

Postoje osnovni entiteti:

- User
- Role
- Patient
- Provider
- Room
- Module
- Service
- Appointment
- ApiKey
- AuditLog
- Supplier
- InventoryItem
- InventoryBatch
- StockLocation
- StockMovement
- PurchaseOrder
- PurchaseOrderLine
- Invoice
- InvoiceLine
- ServiceMaterialTemplate

To je ispravan smjer: ne gradi se samo kalendar, nego operativni model klinike.

### 3. Appointment statusi i source polje su jako važni

Dobra odluka je što termin ima status i izvor narudžbe. To omogućuje kasniju kontrolu je li termin nastao ručno, preko API-ja, AI agenta, call centra, web bookinga, Google Calendara ili vanjskog EMR-a.

### 4. Inventar je ugrađen dovoljno rano

Ovo je presudno. Ako se skladište dodaje naknadno, model se mora lomiti. Ovdje su inventar, batch, LOT, rok trajanja, lokacije, kretanja, narudžbenice i predlošci potrošnje već u početnom modelu.

### 5. FEFO potrošnja je već idejno prisutna

Postoji funkcija za potrošnju po principu first-expiring-first-out. To je ispravna logika za medicinski materijal, filere, lijekove i potrošni materijal.

## Kritični problemi

### 1. Nema pravih migracija

Backend koristi `Base.metadata.create_all()` pri startupu. To je prihvatljivo za demo, ali nije prihvatljivo za sustav koji će imati stvarne pacijente i stvarne račune.

Potrebno:

- uvesti Alembic
- ukloniti automatski `create_all()` iz produkcijskog startupa
- imati verzionirane migracije
- imati seed samo kao eksplicitnu komandu

### 2. RBAC postoji samo površinski

Postoji Role model i helper za zahtijevanje uloga, ali rute dominantno koriste samo `get_current_user`. To znači da se autentificirani korisnik potencijalno može ponašati preširoko.

Potrebno:

- definirati permissione, ne samo role
- uvesti granularna prava: patients.read, patients.write, appointments.write, inventory.adjust, billing.mark_paid, audit.read, admin.manage_users
- AI agent mora imati najmanji mogući scope

### 3. AI agent nije sigurnosno izoliran

Postoji ApiKey model, ali AI endpointi ne smiju koristiti isti auth model kao ljudski korisnici bez posebnih ograničenja.

Potrebno:

- poseban API-key auth za agente
- scopeovi po API ključu
- rate limit
- audit s actor_type: user/api_key/ai_agent/system
- zabrana brisanja i financijskih akcija za AI agenta po defaultu

### 4. Audit log je preslab

Trenutni AuditLog čuva action, entity_type, entity_id i summary. To nije dovoljno.

Potrebno:

- before JSON
- after JSON
- actor_type
- actor_id
- request_id
- ip_address
- user_agent
- correlation_id
- timestamp s timezoneom

Medicolegalno, mora se znati što je točno promijenjeno.

### 5. Validacije termina nisu dovoljne

Kod kreiranja termina ne vidi se zaštita od preklapanja termina za istu sobu ili istog liječnika.

Potrebno:

- spriječiti overlap provider_id + date + time
- spriječiti overlap room_id + date + time
- validirati end_time > start_time
- duration mora odgovarati vremenskom rasponu ili se automatski izračunati
- status mora biti enum, ne slobodni string

### 6. Inventar ima dobar model, ali poslovna logika je preplitka

Trenutno postoje batch i stock movement, ali treba strogo definirati pravila:

- quantity nikada ne smije pasti ispod nule
- movement_type mora biti enum
- transfer mora napraviti dva učinka: skidanje sa stare lokacije i dodavanje na novu lokaciju ili jasno voditi batch/location state
- adjustment mora tražiti razlog
- write-off mora tražiti razlog i potencijalno odobrenje
- purchase receipt mora imati vezu s purchase order line
- invoice i stock consumption ne smiju biti labavo povezani

### 7. `current_stock` je derivirani podatak i može se razići

InventoryItem ima `current_stock`, a InventoryBatch ima quantity. To je praktično za dashboard, ali opasno ako nema transakcijske konzistentnosti.

Potrebno:

- jasno odlučiti je li `current_stock` cache ili source of truth
- source of truth treba biti batch/stock ledger
- recalculate_stock mora biti pozivan transakcijski
- dodati DB constraintove i testove

### 8. Narudžbenice su zasad gotovo samo header

PurchaseOrderLine model postoji, ali API za linije i zaprimanje robe iz linija treba biti ozbiljnije razrađen.

Potrebno:

- endpointi za dodavanje/uređivanje/brisanje PO linija
- partial receive
- receipt creates inventory batches
- povezivanje s dobavljačem, LOT-om, rokom trajanja i nabavnom cijenom

### 9. Računi su samo priprema, ne billing sustav

Invoice i InvoiceLine postoje, ali nedostaje:

- brojčani slijed računa
- porezne stope
- R1 podaci
- statusi: draft/issued/cancelled/paid/partially_paid/refunded
- payment transactions
- fiskalizacijski adapter za RH
- export za računovodstvo

### 10. Frontend inventara je samo dashboard/lista

Frontend ima rute za inventory/suppliers/purchase-orders/invoices, ali inventar treba radne ekrane:

- artikl detalj
- batch detalj
- ulaz robe
- transfer
- otpis
- inventurna korekcija
- predlošci potrošnje po usluzi
- potvrda potrošnje nakon usluge

### 11. Nedostaju testovi

Za ovakav sustav minimalno treba:

- backend unit testovi
- API integration testovi
- test FEFO potrošnje
- test sprječavanja overlap termina
- test auth/permissions
- test audit loga
- frontend smoke testovi

### 12. Nema production security hardeninga

Potrebno:

- sigurni defaulti za JWT_SECRET
- password policy
- refresh token ili kratki access token
- CORS ograničiti po environmentu
- rate limiting
- audit ne smije curiti svima
- backup/restore strategija

## Zaključak

Projekt je na dobrom putu. Najveća vrijednost je to što je inventar rano stavljen u isti domenski model kao termini i usluge. To je ispravno.

Najveći rizik je da se MVP počne koristiti kao stvarni sustav prije nego što se riješe migracije, permissioni, audit, validacije i skladišne transakcije.

Moja preporuka:

1. Ne širiti funkcionalnosti dalje dok se ne stabilizira jezgra.
2. Prvo napraviti migracije, testove, RBAC i audit.
3. Zatim dovršiti appointment overlap i inventory ledger.
4. Tek onda graditi AI agente, fiskalizaciju i cloud deployment.
