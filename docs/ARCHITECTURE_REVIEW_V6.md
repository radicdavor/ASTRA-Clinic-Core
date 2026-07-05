# ASTRA Clinic Core — kritički osvrt v6

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Codex je implementirao značajan dio v5 smjera. Projekt sada ima vidljiv prelazak iz “MVP koji ima logiku” u “MVP koji počinje imati provjerljivost”.

Najvažnije što je sada potvrđeno:

- CI postoji i pokreće backend uz PostgreSQL servis, Alembic migracije, pytest i frontend build/typecheck.
- Test konfiguracija sada ima i SQLite fixture i PostgreSQL fixture preko `TEST_DATABASE_URL`.
- Backend testovi postoje za appointment, inventory, procurement, billing i appointment material rollback.
- Fiscalization boundary je integriran u billing servis.
- Production safety check postoji u configu i poziva se pri startupu.
- Frontend operational gap analiza postoji.
- Minimalni module manifest postoji za gastroenterology.

Moj stav: **v5 je dobar i vrijedan, ali nije potpuni kraj Quality Gatea**. Postoji safety net, ali još je previše plitak na API-layeru i premalo operativan na frontendu.

Sljedeći sprint treba biti **Operational Closure Sprint**: zatvoriti preostale API quality rupe i napraviti tri najvažnija UI workflowa.

## Što je dobro napravljeno

### 1. CI je bitno bolji

`.github/workflows/ci.yml` sada:

- diže PostgreSQL 16 servis
- postavlja `DATABASE_URL`
- postavlja `TEST_DATABASE_URL`
- pokreće Alembic migracije
- pokreće pytest
- radi frontend typecheck
- radi frontend build

To je značajan napredak. Projekt sada ima osnovni CI safety net.

### 2. PostgreSQL integration fixture postoji

`backend/tests/conftest.py` sada ima `pg_db` i `pg_client` fixture koji koriste `TEST_DATABASE_URL`. To je bila glavna kritika v5 i sada je barem arhitektonski adresirana.

Međutim, treba provjeriti koliko testova stvarno koristi `pg_db`/`pg_client`. Samo postojanje fixturea nije isto što i stvarna PostgreSQL coverage.

### 3. Fiscalization boundary je integriran u billing

`billing.py` sada importira `FiscalizationProvider` i `get_fiscalization_provider`, ima `apply_fiscalization_result`, a `issue_invoice` poziva fiscalization flow nakon izdavanja broja računa.

To je pravi arhitektonski potez. Još uvijek nije stvarna hrvatska fiskalizacija, ali granica postoji.

### 4. Production safety check postoji

`config.py` sada ima `APP_ENV`, `validate_production_safety`, provjeru slabog JWT secreta i zabranu localhost/wildcard CORS-a u produkciji. `main.py` poziva `settings.validate_production_safety()` pri startupu.

To je vrlo dobra zaštita od slučajnog glupog deploya.

### 5. Frontend gap analysis postoji

`docs/FRONTEND_OPERATIONAL_GAP_ANALYSIS.md` jasno kaže da frontend još nema:

- purchase order receiving by line
- stock transfer/write-off s razlogom
- complete appointment with material consumption
- draft invoice from appointment
- invoice issue/payment recording
- API key management

I dobro prioritizira top 3:

1. complete appointment with material consumption
2. purchase order receiving
3. invoice issue and payment recording

To je ispravan operativni fokus.

### 6. Modul manifest je krenuo

Postoji barem `backend/app/modules/catalog/gastroenterology/module.json`. To je početak manifest modularnosti, ali još nije stvarni module loader/workflow engine.

## Što još nije dovoljno dobro

### 1. PostgreSQL fixture postoji, ali coverage nije dokazana

CI postavlja PostgreSQL i test fixture ga može koristiti, ali u pregledanim testovima još se jasno vide service-level testovi i SQLite fixture. Potrebno je eksplicitno imati testove koji koriste `pg_db`/`pg_client` za kritične workflowe.

Obavezno PostgreSQL-backed:

- invoice number sequence with `with_for_update`
- FEFO with row locking
- purchase receiving rollback
- appointment completion with material consumption rollback
- migration smoke
- constraints

### 2. API-layer testovi nisu dovoljno vidljivi

Pregledani testovi su uglavnom service-level. To je korisno, ali nije dovoljno za sustav koji će koristiti korisnici, AI agenti i vanjski programi.

Mora se testirati stvarni path:

`HTTP request -> auth/API key -> permission -> route -> service -> DB -> audit`

Prioritetni API testovi:

- inventory adjustment/write-off permission denial
- billing mark-paid permission denial
- API key with AI scopes cannot do inventory/billing actions
- purchase order receive endpoint
- complete appointment with consumption endpoint
- invoice issue/payment endpoint
- audit-log endpoint permission and filters

### 3. AI API key granice moraju biti brutalno testirane

AI agent je moćan samo ako je ograničen. Ne smije moći:

- raditi stock adjustment
- raditi write-off
- označiti račun plaćenim
- čitati audit log
- mijenjati financije

To mora biti pokriveno endpoint testovima, ne samo logikom u glavi.

### 4. Audit rekonstrukcija još treba jače testove

Audit je medicolegalni sloj. Treba dokazati:

- before_json i after_json postoje kod updatea
- request_id se zapisuje
- actor_type je točan
- api_key actor se razlikuje od user actora
- audit filtering radi
- payment, invoice issue, PO receive i write-off stvaraju dovoljno podataka za rekonstrukciju događaja

### 5. Frontend je sada najveći operativni manjak

Backend ima sve više ozbiljnih workflowa, ali frontend gap analiza priznaje da najvažniji dnevni procesi nisu UI-first.

Sljedeći pravi product step nije novi modul, nego:

- završiti termin s potrošnjom materijala
- zaprimiti narudžbenicu po stavkama
- izdati račun i evidentirati uplatu

Bez toga će sustav ostati “API dobar, ordinacija ga ne može glatko koristiti”.

### 6. Module manifest je tek početak

`module.json` postoji, ali treba idempotentni loader koji učitava:

- services
- material_templates
- workflows
- patient instructions
- AI prompts

Bez izvršavanja proizvoljnog plugin koda.

### 7. Nema stvarnog release standarda

Projekt sada treba prijeći na disciplinu:

- changelog
- semantic versioning
- release checklist
- migration checklist
- manual QA checklist
- “demo data only” mode

To je sljedeći korak prije bilo kakve stvarne uporabe.

## Ocjena nakon v5

### Arhitektura

Jaka za fazu projekta.

### Testovi

Dobar početak, ali još nedovoljno API/PostgreSQL integracijski.

### CI

Dobar baseline.

### Sigurnost

Bolja; produkcijski safety check je važan dobitak.

### Billing

Arhitektonski bolji zbog fiscalization boundaryja.

### Frontend

Najveći product gap.

### Modularnost

Početna, ali još nije engine.

## Preporučeni sljedeći sprint

Naziv:

**Operational Closure Sprint**

Cilj:

Zatvoriti preostale quality gate rupe i omogućiti tri ključna dnevna workflowa kroz UI.

Prioriteti:

1. PostgreSQL-backed API integration tests
2. AI API key permission boundary tests
3. audit reconstruction tests
4. endpoint rollback tests
5. frontend workflow: complete appointment with material consumption
6. frontend workflow: purchase order receiving
7. frontend workflow: invoice issue + payment recording
8. module manifest loader foundation
9. release checklist

## Zaključak

V5 je dobar. Projekt je sada dovoljno ozbiljan da treba početi razmišljati kao product maintainer, ne samo kao builder.

Moj čvrst stav: **sljedeći korak mora spojiti backend pouzdanost i operativni UI**. Ako sada kreneš u nove AI agente ili nove medicinske module, riskiraš širinu bez upotrebljivosti. Ako prvo zatvoriš ova tri UI workflowa i API quality gate, ASTRA postaje stvarno upotrebljiv clinic operations MVP.
