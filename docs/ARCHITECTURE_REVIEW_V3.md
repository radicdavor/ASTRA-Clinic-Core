# ASTRA Clinic Core — kritički osvrt v3

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Projekt je nakon prethodnog pregleda napravio značajan skok. Inventory/procurement/billing dio je sada mnogo zreliji nego u v2 stanju.

Najvažnije novo stanje:

- inventory rute sada uglavnom koriste `Actor` + `require_permission`, ne više samo obični `get_current_user`
- endpointi imaju `response_model` za ključne entitete
- purchase order linije postoje i imaju CRUD endpointove
- zaprimanje narudžbenice sada stvarno kreira `InventoryBatch` i `StockMovement`
- računi imaju stavke, payment transaction i draft invoice iz appointmenta
- dodani su check constrainti za negativne količine
- postoji recalculate stock endpoint
- appointment material consumption workflow postoji

To je vrlo dobar napredak. Projekt sada više nije samo “booking + inventar ideja”, nego već ima kostur clinic-ERP-light sustava.

Ali sada ulazimo u fazu gdje će najviše problema biti u rubnim slučajevima, transakcijama, testovima i produkcijskom ponašanju. Drugim riječima: arhitektonski smjer je dobar, ali sada treba dokazati da sustav ne puca u stvarnim scenarijima.

## Što je dobro napravljeno

### 1. Inventory/procurement/billing su prešli na permission model

Inventory rute sada koriste `Actor` i `require_permission`. Primjeri uključuju:

- `inventory.read`
- `inventory.write`
- `inventory.adjust`
- `inventory.transfer`
- `inventory.write_off`
- `procurement.read`
- `procurement.write`
- `billing.read`
- `billing.write`
- `billing.mark_paid`

To je ogroman korak naprijed. AI agent ili običan korisnik više ne bi smio lako doći do destruktivnih operacija bez eksplicitne dozvole.

### 2. Response modeli su dodani

Rute sada koriste Pydantic response modele kao što su:

- `InventoryItemOut`
- `InventoryBatchOut`
- `StockMovementOut`
- `SupplierOut`
- `PurchaseOrderOut`
- `PurchaseOrderLineOut`
- `InvoiceOut`
- `InvoiceLineOut`
- `PaymentTransactionOut`

To je važno jer API mora biti jasan AI agentima i vanjskim integracijama.

### 3. Zaprimanje narudžbenice je sada stvarno zaprimanje robe

Endpoint za receiving sada:

- provjerava narudžbenicu
- provjerava stavke narudžbenice
- sprječava zaprimanje veće količine od naručene
- traži LOT/rok kad je tracking uključen
- kreira `InventoryBatch`
- kreira `StockMovement` tipa `purchase_receipt`
- povećava `quantity_received`
- recalculira stock
- derivira status narudžbenice

To je prava poslovna logika, ne samo status update.

### 4. Billing je sada ozbiljniji

Dodani su:

- `InvoiceLine`
- `PaymentTransaction`
- draft invoice iz appointmenta
- payment endpointi
- automatski recalculation invoice total/payment status
- hrvatski-ready atributi: operator, business_unit, register_id, vat_id, fiscalization_status, fiscalization_reference

To je dobra osnova za kasniju fiskalizaciju.

### 5. DB check constrainti su dobar potez

Postoje constrainti:

- `InventoryItem.current_stock >= 0`
- `InventoryBatch.quantity >= 0`
- `StockMovement.quantity > 0`
- `PurchaseOrderLine.quantity_ordered > 0`
- `InvoiceLine.quantity > 0`
- `PaymentTransaction.amount > 0`

To je nužno za integritet podataka.

## Kritični problemi koji ostaju

### 1. Nema vidljivog test suitea

Ovo je sada najveći problem.

Projekt je ušao u fazu gdje više nije dovoljno da kod “izgleda dobro”. Treba dokazati poslovna pravila testovima.

Bez testova ne znamo:

- radi li FEFO uvijek ispravno
- radi li rollback ako potrošnja materijala zakaže
- radi li partial PO receive u svim kombinacijama
- može li se overpayati račun
- može li AI API key zaobići permissione
- hoće li appointment completion ostaviti inventar u polovičnom stanju ako pukne commit

Moj stav: **sljedeći commit mora biti test infrastructure + kritični backend testovi.** Ne novi moduli.

### 2. Potencijalni bug: `audit_actor` potpis i pozivi izgledaju neusklađeno

Definicija helpera izgleda ovako:

```python

def audit_actor(db, action, entity_type, entity_id, summary, actor, request, before=None, after=None):
    ...
```

Ali barem u dijelu inventory ruta postoje pozivi koji izgledaju kao da je `summary` preskočen ili da je `actor` poslan na mjesto summaryja.

Primjer obrasca koji treba provjeriti:

```python
audit_actor(db, "create", "InventoryItem", item.id, item.name, actor, request, None, snapshot(item))
```

To je ispravno ako je `item.name` summary. Međutim sve pozive treba strojno i testovima provjeriti jer je ova funkcija centralna za audit. Jedan krivi positional argument može dati lažno auditiranje.

Preporuka:

- prebaciti `audit_actor` na keyword-only argumente
- ili barem standardizirati potpis
- dodati test za audit log actor_type/user_id/api_key_id/before/after

### 3. Potencijalni bug: `create_payment` se poziva iz `mark_paid` i radi commit unutar helper endpointa

U `mark_paid` se poziva `create_payment(...)`, a `create_payment` je endpoint funkcija koja sama radi `db.commit()`.

To je antipattern.

Problem:

- endpoint funkcije ne bi smjele služiti kao service funkcije
- nested commit otežava transakcijsku kontrolu
- ako kasnije dio logike pukne, dio promjene već može biti committed

Preporuka:

- izvući payment logiku u service funkciju `record_payment(...)`
- endpoint `create_payment` samo poziva service
- endpoint `mark_paid` isto poziva service
- commit raditi samo na rubu endpointa ili kroz jasno definiranu transaction boundary logiku

### 4. Potencijalni bug: invoice total recalculation nakon dodavanja paymenta

U `create_payment` se nakon `db.flush()` ručno radi:

```python
invoice_obj.payments.append(payment)
```

Ako je SQLAlchemy relationship već povezan preko `invoice_id`, ručno appendanje može biti nepotrebno ili dovesti do duplog objekta u relationship kolekciji u istoj sesiji.

Preporuka:

- koristiti service metodu koja nakon `db.flush()` radi `db.refresh(invoice_obj)` ili ponovno queryja invoice s payments
- testirati da uplata 50 EUR na račun 100 EUR rezultira `partially_paid`, a ne duplim plaćanjem

### 5. `next_invoice_number` nije concurrency-safe

Trenutna logika generira broj iz zadnjeg ID-a:

```python
ASTRA-YYYYMMDD-{last_invoice_id + 1}
```

To nije sigurno u paralelnom radu. Dva zahtjeva mogu dobiti isti broj.

Preporuka:

- dodati `InvoiceNumberSequence` tablicu
- ili koristiti DB sequence
- ili generirati broj tek pri izdavanju računa, ne pri draftu
- draft može imati privremeni interni ID, a službeni broj dobiva tek kad postaje issued

Za hrvatsku fiskalizaciju ovo će kasnije biti jako važno.

### 6. Nedostaje status workflow za invoice

Trenutno se invoice može ažurirati generički. Treba definirati dozvoljene prijelaze.

Primjer:

- draft -> issued
- issued -> paid / partially_paid / cancelled
- paid -> refunded djelomično ili potpuno
- cancelled ne smije primati nove uplate
- issued invoice ne bi smio slobodno mijenjati stavke bez storna/novog dokumenta

Preporuka:

- dodati service funkcije za status transitions
- blokirati direktan update kritičnih polja nakon issued statusa

### 7. Appointment material consumption treba eksplicitniji transaction boundary

Endpoint `complete-with-consumption` potroši materijale i zatim stavlja appointment na completed.

To je ispravno, ali mora biti testirano kao atomic operation:

- ako jedna stavka nema dovoljno zalihe, nijedna zaliha se ne smije skinuti
- appointment ne smije prijeći u completed
- audit ne smije ostati polovičan

Preporuka:

- service funkcija `complete_appointment_with_consumption(...)`
- test rollbacka s dvije stavke, gdje druga nema dovoljno zalihe

### 8. Variable material consumption je još konceptualno osjetljiv

Kod automatski konzumira samo required i non-variable templatee ako payload nije poslan. To je dobro, ali treba jasnije ponašanje:

- propofol kao variable ne smije se automatski skinuti
- required + variable mora tražiti unos količine prije completiona
- optional materijal se ne skida bez korisničkog izbora

Preporuka:

- response suggest endpoint mora jasno označiti: auto_consumable, requires_user_quantity, optional
- complete endpoint mora vratiti 422 ako postoji required variable item bez unesene količine

### 9. Purchase order total recalculation treba robusniju service funkciju

Kod ručno recalculira total kroz `sum(order.lines)`. To je u redu za MVP, ali treba centralizirati u `recalculate_purchase_order_total(order)`.

Također treba paziti na SQLAlchemy relationship stanje nakon delete/flush.

### 10. Nedostaje CI

Projekt treba GitHub Actions minimalno za:

- backend lint/type check
- backend pytest
- frontend build
- frontend tests ako postoje
- docker compose smoke test

Bez CI-ja svaka sljedeća Codex iteracija može nehotice slomiti postojeće funkcionalnosti.

### 11. Nedostaje production secret discipline

README još pokazuje default admin lozinku `astra123` i lokalni setup. To je OK za razvoj, ali treba jasno odvojiti:

- dev credentials
- production env
- obavezna promjena JWT_SECRET
- obavezna promjena admin lozinke
- CORS u produkciji
- backup/restore

### 12. Nema jasnog licensing/compliance stava

Ako je projekt open-source i medicinski, treba rano odlučiti:

- AGPL-3.0 ako želiš zaštititi open-source karakter i spriječiti zatvorene SaaS forkove
- Apache-2.0/MIT ako želiš maksimalnu adopciju

Za medicinske podatke treba dodati i jasno upozorenje:

- nije certificirani medicinski uređaj
- nije certificirani EMR
- produkcijska uporaba zahtijeva GDPR, sigurnosnu i pravnu validaciju

## Najvažniji sljedeći sprint

Moj vrlo jasan prioritet:

1. **Test infrastructure + backend business tests**
2. **Refactor endpoint logike u service layer**
3. **Concurrency-safe invoice numbering**
4. **Atomic appointment material consumption**
5. **CI pipeline**
6. **README security/compliance update**

Ne bih sada radio nove module. Ne bih sada radio veliki frontend redizajn. Ne bih sada dodavao Google Calendar. Prvo treba dokazati da postojeća jezgra drži vodu.

## Zaključak

Projekt je sada na vrlo dobrom putu. Najveća vrijednost je što su scheduling, inventar, nabava i billing počeli biti povezani u jedan operativni sustav klinike.

Ali sada je došao trenutak kada razvoj mora postati stroži. Sljedeći Codex prompt mora biti manje “dodaj feature” i više “dokaži ispravnost, testiraj, refaktoriraj, zatvori transakcije”.

Ako se to napravi, ASTRA Clinic Core će iz demo-MVP-a prijeći u realan temelj za lokalni clinic OS.
