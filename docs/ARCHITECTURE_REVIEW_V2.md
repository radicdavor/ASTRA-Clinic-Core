# ASTRA Clinic Core — kritički osvrt v2

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Repozitorij je u odnosu na raniji pregled značajno napredovao. Ovo više nije samo konceptualni scaffold. Core dio sada pokazuje ozbiljniji smjer:

- README navodi Alembic migracije, permission-based RBAC, strukturirani audit, conflict validation i scoped API key autentikaciju za AI agente.
- `main.py` više nema startup `create_all()` nego ima request-id middleware.
- domenski model sada ima `Permission`, `role_permissions`, `ApiKey.scopes`, prošireni `AuditLog`, appointment enum-e i stock movement enum-e.
- core appointment rute koriste `require_permission` i strukturirani audit s before/after snapshotima.
- appointment validacija sprječava preklapanje liječnika i sobe.
- inventar ima bolju FEFO logiku, zaključavanje batch redova s `with_for_update()`, zaštitu od negativne potrošnje i transfer logiku.

Moj zaključak: **jezgra se kreće u pravom smjeru, ali projekt je sada u opasnoj međufazi** — dovoljno izgleda kao pravi sustav da bi ga netko mogao početi koristiti, ali inventar, nabava, računi, testovi i produkcijska sigurnost još nisu dovoljno zatvoreni.

## Što je sada dobro

### 1. README sada jasno opisuje cilj i trenutno stanje

README ispravno definira projekt kao open-source modularnu jezgru za kliniku: pacijenti, naručivanje, dnevni raspored, tijek pacijenta, API integracije, audit log, RBAC, inventar, nabava i priprema naplate. To je dobar strateški okvir.

### 2. Alembic je ušao u dokumentirani workflow

README navodi da backend entrypoint automatski pokreće `alembic upgrade head` i seed komandu. To je pravi smjer. Potrebno je još provjeriti i testirati migracije kao dio CI-ja.

### 3. Request ID middleware je dobar potez

`main.py` sada dodaje `X-Request-ID` u svaki response. To je važno za audit, debugging i kasniju integraciju s AI agentima i vanjskim sustavima.

### 4. Permission-based RBAC je uveden u model

Model sada ima:

- `Permission`
- `role_permissions`
- `Role.permissions`
- `ApiKey.scopes`

To je puno bolje od role-only pristupa.

### 5. Audit log je bitno ozbiljniji

Audit sada podržava:

- actor_type
- actor_user_id
- actor_api_key_id
- before_json
- after_json
- request_id
- ip_address
- user_agent

To je nužna razina za medicinski i operativni sustav.

### 6. Appointment conflict validation postoji

Funkcija `validate_appointment_payload` provjerava:

- status enum
- source enum
- end_time > start_time
- preklapanje provider termina
- preklapanje room termina
- blokirajuće statuse

To je jedan od najvažnijih ispravaka.

### 7. FEFO inventar je bolji nego prije

Inventar sada:

- provjerava pozitivne količine
- provjerava dostupnu zalihu prije potrošnje
- koristi `with_for_update()` kod FEFO potrošnje
- ima `StockMovementType`
- ima transfer_out i transfer_in logiku

To je ispravan smjer za medicinsko skladište.

## Najveće slabosti koje ostaju

### 1. Inventory, procurement i billing nisu još prebačeni na permission-based actor model

Core rute koriste `require_permission`, ali inventory rute i dalje većinom koriste `get_current_user`. To znači da je sigurnost sada neujednačena.

Problem:

- pacijenti i termini su relativno dobro zaštićeni
- skladište, dobavljači, narudžbenice i računi nisu na istoj razini

Potrebno:

- `inventory.read`
- `inventory.write`
- `inventory.adjust`
- `inventory.write_off`
- `procurement.read`
- `procurement.write`
- `billing.read`
- `billing.write`
- `billing.mark_paid`

AI agent ne smije imati pristup skladišnim korekcijama, otpisima ni plaćanju računa.

### 2. Audit nije konzistentan kroz sve rute

Core rute auditiraju before/after snapshot. Inventory rute još često auditiraju samo summary i user_id.

Potrebno:

- inventory create/update/delete mora imati before/after
- stock movement mora imati actor_type
- purchase order i invoice promjene moraju imati before/after
- svaki kritični financijski i skladišni događaj mora biti auditiran na istoj razini kao appointment

### 3. Purchase order receiving je još nedovoljno ozbiljan

Endpoint `/purchase-orders/{order_id}/receive` trenutno izgleda kao da samo promijeni status narudžbenice u `received`. To nije stvarno zaprimanje robe.

Stvarno zaprimanje mora:

- imati PO linije
- podržati partial receive
- stvoriti InventoryBatch
- stvoriti StockMovement `purchase_receipt`
- upisati LOT/batch
- upisati expiration_date
- upisati lokaciju skladišta
- ažurirati `quantity_received`
- ažurirati status narudžbenice u partially_received ili received

### 4. Računi su još samo osnovna priprema

Invoice postoji, ali pravi billing workflow još nije dovoljno razrađen.

Nedostaje:

- InvoiceLine API
- payment transaction model
- invoice number generator
- draft invoice from appointment
- statusi issued/cancelled/paid/partially_paid/refunded
- priprema za hrvatsku fiskalizaciju
- adapter pattern za fiscalization provider

### 5. `current_stock` kao cache treba strožu zaštitu

InventoryItem.current_stock postoji i recalculate se poziva u nekim mjestima. To je prihvatljivo kao cache, ali mora biti strogo definirano da batch ledger ostaje source of truth.

Potrebno:

- DB check constraint da quantity >= 0 gdje je moguće
- integracijski test da zbroj batchova odgovara current_stock
- repair endpoint ili admin command za recalculation

### 6. Transfer batch logika potencijalno umnožava batch zapise

Trenutni transfer stvara novi target batch s istim lotom i rokom na novoj lokaciji. To je prihvatljivo ako je namjerno, ali treba definirati pravilo spajanja:

- ako na ciljnoj lokaciji već postoji isti item + lot + expiration + purchase_price + supplier, treba li povećati postojeći batch ili uvijek stvarati novi?

Za rad skladišta je čišće imati merge opciju, ali zbog audita je prihvatljivo i uvijek stvarati novi batch. Bitno je da pravilo bude eksplicitno i testirano.

### 7. Nema dovoljno response_model shema

FastAPI bez response_modela brzo postane nekonzistentan. Za AI agente i vanjske integracije OpenAPI mora biti precizan.

Potrebno:

- output sheme za Patient, Appointment, Service, InventoryItem, InventoryBatch, StockMovement, PurchaseOrder, Invoice
- response_model na glavnim rutama
- OpenAPI primjeri

### 8. Nema vidljivog test suitea

Bez testova ovaj projekt ne smije ići prema stvarnoj uporabi.

Minimalni testovi:

- login
- permission denial
- appointment overlap
- FEFO across two batches
- insufficient stock rollback
- transfer preserves total stock
- purchase order partial receive
- invoice draft from appointment
- audit before/after
- AI API key scopes

### 9. Frontend treba pratiti backend sigurnost i workflow

Frontend ima stranice, ali treba postati operativni alat, ne samo popis.

Potrebno:

- završetak termina s potvrdom potrošnje materijala
- zaprimanje robe po narudžbenici
- transfer skladišta
- otpis s razlogom
- inventurna korekcija s razlogom
- račun iz termina
- audit filteri
- upozorenja za nisku zalihu i rokove

### 10. Medicinska modularnost još nije prava modularnost

Model ima Module i Service, ali “modul” još nije plugin/workflow sustav.

Potrebno:

- module manifest JSON
- service templates
- material templates
- workflow steps
- patient instructions
- AI prompts per module

Primjeri modula:

- gastroenterology
- endoscopy
- dermatology_aesthetics
- mounjaro
- h_pylori
- sibo_imo
- colonoscopy_prep

## Prioriteti za sljedeći razvoj

### Prioritet 1 — izjednačiti sigurnost inventory/procurement/billing ruta s core rutama

Sve inventory, procurement i invoice rute moraju koristiti actor + permission model.

### Prioritet 2 — dovršiti pravi purchase order receiving

Bez toga nabava nije stvarni modul nego samo tablica narudžbenica.

### Prioritet 3 — dodati testove prije daljnjeg širenja

Prvo pokriti appointment konflikt, FEFO i permissione.

### Prioritet 4 — billing pretvoriti iz osnovne tablice u workflow

Račun mora moći nastati iz termina i usluge, imati stavke i payment transaction.

### Prioritet 5 — otvoriti modularni workflow engine

Tek tada ASTRA postaje modularna platforma, a ne samo scheduling + inventory aplikacija.

## Zaključak

Smjer je dobar. Projekt sada ima ozbiljniji core nego prije. Najveća greška sada bi bila širiti featuree bez zatvaranja transakcijske ispravnosti, testova i permissionsa.

Moj čvrst stav: **sljedeći razvojni sprint mora biti security + inventory/procurement correctness sprint**, ne novi UI i ne novi AI featurei.

AI agent će biti koristan tek kada sustav ima jasne dozvole, sigurne API ključeve, audit i transakcijski korektan inventar. Inače AI samo ubrzava greške.
