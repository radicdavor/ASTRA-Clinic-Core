# ASTRA Clinic Core — kritički osvrt v5

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Codex je doista implementirao velik dio v4 smjera. Ovo više nije samo backend MVP bez dokaza; sada postoje CI, backend testovi, security dokumentacija, deployment bilješke, backup/restore dokumentacija i fiskalizacijski stub.

Najvažnije što sada postoji:

- GitHub Actions CI s PostgreSQL servisom, Alembic migracijama, backend pytestom i frontend buildom.
- Backend pytest infrastruktura.
- Testovi za appointment konflikt.
- Testovi za FEFO, transfer, recalculation i inventory edge caseove.
- Testovi za procurement receiving, partial receive i rollback prije mutacije.
- Testovi za billing, invoice issue, partial/full payment i overpayment.
- Test za failed appointment material consumption bez mutacije zalihe i appointment statusa.
- Fiscalization provider boundary s Noop providerom i Croatia stubom.
- SECURITY.md.
- Google Cloud deployment notes.
- Backup/restore dokumentacija.

Moj stav: **v4 je dobro odrađen, ali sada počinje najopasnija faza — testovi postoje, ali još nisu dovoljno reprezentativni za produkciju.**

Sljedeći sprint mora biti **Quality Gate Sprint**: poboljšati dubinu testova, prebaciti najkritičnije integracijske testove s SQLite-a na PostgreSQL, pokriti API-layer permissione i audit, te tek onda širiti UI i modularnost.

## Što je dobro implementirano

### 1. CI je prisutan i radi u pravom smjeru

`.github/workflows/ci.yml` pokreće backend job s PostgreSQL 16 servisom, instalira backend dependencyje, pokreće Alembic migracije i zatim pytest. Frontend job instalira npm dependencyje i pokreće build.

To je velika prekretnica. Projekt sada ima osnovni safety net.

### 2. Testovi sada postoje

Postoje testovi za:

- appointment validation
- provider overlap
- room overlap
- cancelled appointment non-blocking behavior
- FEFO potrošnju
- insufficient stock
- stock transfer
- stock recalculation
- billing total recalculation
- invoice issuing
- overpayment rejection
- partial/full payment
- purchase receiving
- over-receive rejection
- failed receive without mutation
- failed appointment material consumption without mutation

To je ogroman napredak u odnosu na v4 stanje.

### 3. Fiskalizacija je dobro postavljena kao boundary, ne kao lažna implementacija

`backend/app/services/fiscalization.py` uvodi:

- `FiscalizationResult`
- `FiscalizationProvider`
- `NoopFiscalizationProvider`
- `CroatiaFiscalizationProviderStub`

To je ispravno. Još ne treba implementirati stvarnu hrvatsku fiskalizaciju; prvo treba čistu granicu.

### 4. Security i deployment dokumentacija postoje

`SECURITY.md`, `docs/DEPLOYMENT_GOOGLE_CLOUD.md` i `docs/BACKUP_RESTORE.md` sada daju minimalni produkcijski okvir.

Posebno je dobro što se eksplicitno navodi da projekt nije certificirani EMR niti medicinski uređaj.

## Najvažniji problemi koji ostaju

### 1. Testovi koriste SQLite fixture, iako CI ima PostgreSQL servis

`backend/tests/conftest.py` koristi `sqlite://` i `StaticPool`. To je korisno za brze unit testove, ali nije dovoljno za domenu koja ovisi o:

- PostgreSQL ponašanju
- Alembic migracijama
- row lockingu
- `with_for_update()`
- constraintima
- transakcijskom ponašanju

Ovo je sada glavni tehnički dug test suitea.

Preporuka:

- zadržati SQLite testove za brze unit testove
- dodati PostgreSQL integration test mode
- CI treba pokretati barem kritične inventory/procurement/billing/transaction testove na PostgreSQL-u

### 2. Testovi su previše service-level, a premalo API-level

Mnogo testova direktno zove service funkcije. To je dobro za domensku logiku, ali ne dokazuje da API sloj radi ispravno.

Potrebni su API tests za:

- auth
- permission denial
- AI API key scopeove
- appointment create/update endpoint
- inventory write-off endpoint
- purchase receive endpoint
- invoice issue/payment endpoint
- audit-log endpoint

Drugim riječima: treba testirati stvarni put korisnik/API agent → endpoint → permission → service → DB → audit.

### 3. RBAC i AI API key testovi nisu dovoljno vidljivi

V4 je tražio detaljne permission testove. U pregledanim testovima nisu vidljivi puni testovi za:

- AI key without inventory.adjust
- AI key without billing.mark_paid
- receptionist cannot write off stock
- inventory manager cannot mark invoice paid
- billing user cannot write off stock
- audit log requires audit.read

Ovo treba postati prioritet jer AI agent bez dobro testiranih scopeova predstavlja realan rizik.

### 4. Audit tests još nisu dovoljno duboki

Postoje audit pozivi u kodu, ali testovi moraju dokazati:

- before_json i after_json kod updatea
- actor_type kod API key akcije
- audit kod inventory write-offa
- audit kod purchase receivea
- audit kod invoice issue/paymenta
- audit filtering

Audit je medicolegalni sloj, ne dekoracija.

### 5. Transaction rollback testovi su još preplitki

Dobar početak postoji: failed material consumption i failed purchase receive. Ali treba eksplicitno testirati i rollback na API razini.

Kritično:

- endpoint `complete-with-consumption` ne smije ostaviti parcijalne stock movemente
- endpoint `purchase-orders/{id}/receive` mora biti atomaran
- endpoint za invoice payment above total ne smije promijeniti invoice status
- stock transfer failure ne smije promijeniti source batch

### 6. CI ne radi frontend typecheck/testove

Frontend job radi `npm run build`, što je dobro, ali treba provjeriti postoji li TypeScript check ili lint. Ako ne postoji, dodati minimalno:

- `npm run typecheck`
- eventualno `npm run lint`

### 7. Fiscalization stub nije povezan s invoice issuing workflowom

Sam stub postoji, ali treba provjeriti poziva li se pri issue invoice workflowu. Ako nije, sljedeći korak je dodati adapter poziv kao Noop bez vanjskih requestova i auditirati pokušaj.

### 8. Frontend operational workflows vjerojatno još nisu zatvoreni

Nakon testova treba provjeriti UI za:

- PO receiving po stavkama
- stock transfer
- write-off s razlogom
- complete appointment with material consumption
- invoice issue
- record payment
- audit filtering
- API key management

Backend sada ima logiku, ali klinika treba radni UI.

### 9. Modul manifest loader još vjerojatno nije napravljen

To je prihvatljivo. Modularnost treba doći tek nakon quality gatea. Ali sljedeći sprint može pripremiti minimalni manifest loader bez izvršnog plugin koda.

## Prioriteti za v5

### Prioritet 1 — PostgreSQL integration tests

Dodati test setup koji koristi PostgreSQL URL iz environmenta. CI već ima Postgres servis, ali testovi ga moraju stvarno koristiti.

### Prioritet 2 — API permission tests

Testirati stvarne HTTP endpointove s različitim korisnicima i API ključevima.

### Prioritet 3 — audit correctness tests

Dokazati before/after, actor_type, request_id i filtering.

### Prioritet 4 — transaction rollback na endpoint razini

Ne samo service-level. Stvarni API endpointi moraju biti atomarni.

### Prioritet 5 — fiscalization stub integration

Noop provider treba biti spojen u invoice issuing workflow, bez vanjskih poziva.

### Prioritet 6 — frontend operational coverage

Tek nakon gore navedenog.

## Moja ocjena nakon v4 implementacije

### Arhitektura

Vrlo dobra.

### Backend domena

Sada jaka MVP jezgra.

### Testovi

Dobar početak, ali nedovoljno duboko i previše SQLite/service-level.

### CI

Postoji i dobar je za početak.

### Sigurnost

Bolja dokumentacijski i arhitektonski, ali permission testovi moraju biti stroži.

### Produkcija

Još nije spremno za stvarne pacijente.

### Sljedeći korak

Quality Gate Sprint.

## Zaključak

V4 je odrađen dobro. Projekt je sada prešao prag gdje se više ne smije raditi samo “još funkcija”.

Najveća opasnost sada nije nedostatak featurea, nego lažan osjećaj sigurnosti jer testovi postoje. Testovi su potrebni, ali moraju biti reprezentativni: PostgreSQL, API layer, permission layer, audit i rollback.

Moj čvrst stav: **v5 mora biti Quality Gate Sprint prije bilo kakve ozbiljne medicinske modularnosti ili AI automatizacije.**
