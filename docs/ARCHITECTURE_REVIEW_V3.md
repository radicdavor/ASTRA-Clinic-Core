# ASTRA Clinic Core — kritički osvrt v3

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Repozitorij je ponovno značajno napredovao u odnosu na prethodni pregled. Najvažnije: slabosti koje su ranije bile najveći problem sada su djelomično ili velikim dijelom adresirane.

Sada postoje jasni tragovi da su implementirani:

- sigurnosna napomena u README-u
- Alembic workflow
- permission-based RBAC
- scoped API key za AI agente
- strukturirani audit s request ID-jem
- inventory/procurement/billing rute s `Actor + require_permission`
- response modeli na velikom dijelu inventory ruta
- purchase order lines i stvarno zaprimanje robe
- stvaranje InventoryBatch i StockMovement pri zaprimanjima
- billing servis s draft računom iz termina, linijama računa, izdavanjem računa i payment transactions
- FEFO potrošnja i merge transfer batch logika

Moj stav: **projekt sada prelazi iz “dobrog scaffolda” u rani, ali ozbiljan clinic-operations MVP**.

Još uvijek nije spreman za stvarnu kliničku upotrebu, ali više nije samo skica. Sljedeći sprint mora biti: testovi, CI, production hardening, OpenAPI stabilizacija i modularni workflow engine.

## Što je sada odlično

### 1. README ima sigurnosnu ogradu

README sada jasno kaže da su zadani korisnik, lozinka i lokalne Docker postavke samo za razvoj, da treba promijeniti admin lozinku, postaviti jak JWT_SECRET, ograničiti CORS, koristiti HTTPS, backup PostgreSQL baze i napraviti GDPR/access-control provjeru. Također eksplicitno kaže da ASTRA Clinic Core nije certificirani EMR ni medicinski uređaj.

To je važno jer ovaj projekt lako može izgledati “spreman” prije nego što to stvarno jest.

### 2. Core feature set je jasno dokumentiran

README navodi pacijente, termine, Alembic migracije, RBAC, audit, conflict validation, scoped API key za AI agente, inventar, nabavu, naplatu, predloške potrošnje i FEFO potrošnju.

To je ispravno pozicioniranje projekta: operativni sloj klinike, ne puni EMR.

### 3. Inventory/procurement/billing rute su sada sigurnosno bolje

Inventory route file sada koristi:

- `Actor`
- `require_permission`
- response modele
- `audit_actor`
- permissione za inventory, procurement i billing

Ovo je veliki skok u odnosu na v2. Više nije prihvatljivo govoriti da je sigurnost samo u core rutama; sada se sigurnosni model počeo širiti na skladište, nabavu i račune.

### 4. Purchase receiving sada ima stvarnu poslovnu logiku

`services/procurement.py` sada validira stavke, količine, LOT, rok trajanja, over-receive i zatim stvara:

- InventoryBatch
- StockMovement `purchase_receipt`
- ažurira `quantity_received`
- recalculira stock
- derivira status narudžbenice

Ovo je točno ono što modul nabave mora raditi.

### 5. Billing servis je mnogo zreliji

`services/billing.py` sada ima:

- draft invoice iz appointmenta
- invoice line total calculation
- invoice total recalculation
- invoice issuing
- invoice number sequence
- payment transactions
- partial/paid status logiku
- zaštitu da se linije mijenjaju samo na draft računu
- zaštitu od uplate preko ukupnog iznosa

To je dobar MVP foundation za kasniju hrvatsku fiskalizaciju.

### 6. Inventory service je ozbiljniji

`services/inventory.py` sada ima:

- `ensure_positive`
- `recalculate_stock`
- `recalculate_all_stock`
- FEFO s `with_for_update()`
- insufficient stock guard
- transfer koji pokušava mergeati u postojeći target batch ako postoji isti item/lot/expiration/location/price/supplier

To je već razumno skladišno ponašanje za MVP.

## Najvažnije preostale slabosti

### 1. Nema vidljivog test suitea

Pretraga nije pokazala pytest/test/CI datoteke. Ovo je sada najveći blocker.

Bez testova ne smije se dalje širiti funkcionalnost.

Minimalno treba testirati:

- appointment overlap
- AI API key scopes
- permission denial
- FEFO across multiple batches
- insufficient stock rollback
- stock transfer preserves total stock
- purchase order partial receive
- over-receive rejection
- invoice draft from appointment
- invoice issue
- payment transaction
- audit before/after

### 2. Nema CI/CD baselinea

Treba dodati GitHub Actions workflow za:

- backend lint/type check
- backend tests
- frontend build
- migration smoke test
- docker compose smoke test

Bez toga Codex može brzo napraviti regresije koje nitko ne vidi.

### 3. Fiscalization je još konceptualna rupa

Billing servis je dobar početak, ali hrvatski računovodstveni/fiskalizacijski kontekst nije riješen.

Za sada ne treba implementirati stvarnu fiskalizaciju, ali treba dodati adapter granicu:

- `FiscalizationProvider`
- `NoopFiscalizationProvider`
- `CroatiaFiscalizationProvider` kao stub
- status polja i greške
- audit svih pokušaja fiskalizacije

### 4. GDPR/access control nije dovoljno duboko modeliran

README upozorava na GDPR, ali aplikacija mora imati stvarne kontrole:

- user management
- deactivation users
- password reset flow
- session/token expiration
- access log za čitanje osjetljivih podataka, ne samo izmjene
- export pacijentovih podataka
- soft delete ili retention model

### 5. OpenAPI treba stabilizirati za vanjske integracije

Response modeli se pojavljuju u inventory rutama, ali treba sustavno proći sve rute.

Vanjski programi i AI agenti trebaju stabilne sheme:

- PatientOut
- AppointmentOut
- FreeSlotOut
- InventoryItemOut
- PurchaseOrderOut
- InvoiceOut
- AuditLogOut
- error model

### 6. Modul medical workflow još nije pravi plugin sustav

Još uvijek su `Module` i `Service` više katalog nego pravi modularni workflow engine.

ASTRA treba modularnost na razini:

- module manifest
- services
- material templates
- patient instructions
- workflow steps
- AI prompts
- post-procedure tasks
- reminders

### 7. Frontend vjerojatno zaostaje za backendom

Backend sada ima napredniju logiku od UI-ja. Treba UI za stvarne dnevne procese:

- zaprimanje narudžbe po stavkama
- partial receive
- završetak termina s materijalnom potrošnjom
- izdavanje računa
- dodavanje uplata
- audit filteri
- AI API key management

### 8. Potrebna je domain-level transakcijska disciplina

Neki servisi rade više promjena u istoj operaciji. Treba eksplicitno testirati rollback:

- ako FEFO potrošnja padne, appointment ne smije biti completed
- ako receive PO padne na trećoj stavci, prve dvije se ne smiju zaprimiti
- ako invoice payment padne, status računa se ne smije djelomično promijeniti

### 9. Nedostaje production hardening

Treba dodati:

- sigurniji token lifetime
- refresh token ili jasna odluka da ga nema
- password policy
- rate limit za login i API key
- CORS per environment
- backup/restore script
- deployment notes za Google Cloud Run + Cloud SQL
- secrets handling

## Preporučeni sljedeći sprint

Moj čvrst prijedlog: **ne dodavati nove medicinske module dok se ne napravi test + CI + hardening sprint**.

Redoslijed:

1. test suite
2. CI workflow
3. OpenAPI response model cleanup
4. transaction/rollback tests
5. fiscalization adapter stub
6. frontend operational flows
7. module manifest engine

## Ocjena stanja

### Arhitektura

Dobra. Smjer je ispravan.

### Backend core

Solidan za MVP.

### Inventory/procurement

Sada više nije samo model nego stvarni početak ERP-light modula.

### Billing

Dobar MVP foundation, ali još nije računovodstveno/fiskalizacijski sustav.

### Sigurnost

Dobar napredak, ali treba produkcijski hardening.

### Testovi

Najveća praznina.

### Modularnost

Konceptualno dobra, implementacijski još plitka.

## Zaključak

ASTRA Clinic Core sada ima smisla dalje razvijati kao ozbiljan open-source clinic operations projekt. Najbolja odluka bila je da inventar, nabava i billing nisu ostavljeni za kasnije, nego su ušli rano u model.

Najveći rizik sada je brzina: ako se nastavi dodavati feature po feature bez testova, za mjesec dana dobit ćemo puno koda kojem se ne može vjerovati.

Sljedeći Codex zadatak mora biti hladan, inženjerski i dosadan: testovi, CI, stabilizacija API-ja, transakcije, sigurnost. Tek nakon toga treba širiti medicinske module i AI automatizaciju.
