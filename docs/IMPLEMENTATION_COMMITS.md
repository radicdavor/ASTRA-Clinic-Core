# ASTRA Clinic Core — plan commitova za Codex

Ovaj dokument služi kao razvojni plan. Svaki odjeljak je zamišljen kao jedan smisleni commit ili mali pull request.

## Commit 1 — Stabilize project structure

**Commit message:** `chore: stabilize backend and frontend structure`

Zadaci:

- Provjeriti da se `docker compose up --build` pokreće bez greške.
- Dodati `.env.example` s jasnim varijablama.
- Dodati backend i frontend healthcheck.
- Dodati `Makefile` ili `justfile` s komandama:
  - `make dev`
  - `make test`
  - `make migrate`
  - `make seed`
  - `make lint`
- Dokumentirati lokalno pokretanje.

Acceptance criteria:

- Novi developer može pokrenuti sustav u manje od 10 minuta.
- API docs su dostupni na `/docs`.
- Frontend se otvara bez ručnih izmjena.

---

## Commit 2 — Add Alembic migrations

**Commit message:** `feat: add alembic database migrations`

Zadaci:

- Uvesti Alembic.
- Generirati inicijalnu migraciju za sve postojeće modele.
- Ukloniti automatski `Base.metadata.create_all()` iz produkcijskog startupa.
- Dodati zasebnu seed komandu.
- Docker entrypoint mora izvršiti migracije prije starta aplikacije.

Acceptance criteria:

- Baza nastaje preko migracija, ne preko `create_all()`.
- Ponovno pokretanje ne duplicira seed podatke.
- Migracije rade na praznoj PostgreSQL bazi.

---

## Commit 3 — Strengthen auth and RBAC

**Commit message:** `feat: add permission-based access control`

Zadaci:

- Dodati model `Permission`.
- Dodati vezu Role -> Permissions.
- Definirati inicijalne role:
  - admin
  - physician
  - nurse
  - receptionist
  - inventory_manager
  - billing
  - ai_agent
- Definirati permissione:
  - patients.read
  - patients.write
  - appointments.read
  - appointments.write
  - appointments.cancel
  - inventory.read
  - inventory.write
  - inventory.adjust
  - procurement.write
  - billing.read
  - billing.write
  - billing.mark_paid
  - audit.read
  - admin.manage_users
- Zamijeniti generički `get_current_user` na kritičnim rutama s permission dependencyjem.

Acceptance criteria:

- AI agent ne može čitati audit log.
- Recepcija ne može raditi inventory write-off.
- Inventory manager ne može označavati račune plaćenima.

---

## Commit 4 — Improve audit log

**Commit message:** `feat: add structured audit logging`

Zadaci:

- Proširiti `AuditLog`:
  - actor_type
  - actor_user_id
  - actor_api_key_id
  - action
  - entity_type
  - entity_id
  - before_json
  - after_json
  - summary
  - request_id
  - ip_address
  - user_agent
  - created_at
- Dodati middleware za request_id.
- Auditirati create/update/delete s before/after snapshotom.
- Dodati filtriranje audit loga po entity_type, actoru, datumu i akciji.

Acceptance criteria:

- Svaka promjena termina bilježi staro i novo stanje.
- Audit log je čitljiv samo korisnicima s `audit.read`.

---

## Commit 5 — Harden appointment scheduling

**Commit message:** `feat: add appointment conflict validation`

Zadaci:

- Validirati:
  - end_time > start_time
  - duration_minutes odgovara razlici start/end ili se automatski računa
  - status je enum
  - source je enum
- Spriječiti preklapanje termina za istog liječnika.
- Spriječiti preklapanje termina za istu sobu.
- Dodati endpoint:
  - `GET /api/appointments/conflicts`
  - `GET /api/ai/free-slots`
- Dodati opciju override samo za admina.

Acceptance criteria:

- Nije moguće slučajno naručiti dva pacijenta u istu sobu u isto vrijeme.
- Nije moguće slučajno naručiti liječnika na dva mjesta istovremeno.
- AI agent koristi free-slots endpoint prije kreiranja termina.

---

## Commit 6 — Inventory ledger correctness

**Commit message:** `feat: enforce inventory ledger rules`

Zadaci:

- Uvesti enum za movement_type:
  - purchase_receipt
  - consumption
  - transfer_out
  - transfer_in
  - adjustment
  - write_off
  - return_to_supplier
- Zabraniti negativne količine.
- Batch quantity ne smije pasti ispod nule.
- Stock movement mora imati razlog za adjustment/write_off.
- Transfer mora kreirati konzistentno skidanje i dodavanje.
- `current_stock` tretirati kao cache koji se recalculira iz batchova.
- Dodati transakcije oko svih skladišnih promjena.

Acceptance criteria:

- Nije moguće potrošiti više materijala nego što postoji.
- Transfer ne gubi količinu.
- Dashboard zalihe odgovara zbroju batch quantity vrijednosti.

---

## Commit 7 — Purchase order lines and receiving

**Commit message:** `feat: add purchase order lines and receiving workflow`

Zadaci:

- Dodati API za PO linije:
  - `POST /api/purchase-orders/{id}/lines`
  - `PATCH /api/purchase-orders/{id}/lines/{line_id}`
  - `DELETE /api/purchase-orders/{id}/lines/{line_id}`
- Implementirati partial receive.
- Zaprimanje robe mora stvoriti InventoryBatch.
- Zaprimanje robe mora stvoriti StockMovement tipa `purchase_receipt`.
- PO statusi:
  - draft
  - ordered
  - partially_received
  - received
  - cancelled

Acceptance criteria:

- Narudžbenica može imati više stavki.
- Može se zaprimiti samo dio narudžbe.
- Zaprimljena roba ulazi u skladište s LOT-om, rokom i lokacijom.

---

## Commit 8 — Service material consumption workflow

**Commit message:** `feat: add appointment material consumption workflow`

Zadaci:

- Endpoint `GET /api/appointments/{id}/suggest-material-consumption` mora vratiti predložene materijale iz service templatea.
- Endpoint `POST /api/appointments/{id}/consume-materials` prima stvarnu potrošnju.
- Endpoint `POST /api/appointments/{id}/complete-with-consumption`:
  - validira termin
  - predlaže potrošnju
  - omogućuje override
  - FEFO skida materijal
  - mijenja status termina u completed
  - auditira sve
- Frontend ekran nakon završetka usluge: “Potrošen materijal”.

Acceptance criteria:

- Kolonoskopija u sedaciji predlaže kanilu, rukavice i propofol kao varijabilnu potrošnju.
- HarmonyCa tretman predlaže HarmonyCa, kanilu, iglu i rukavice.
- Korisnik može izmijeniti potrošnju prije knjiženja.

---

## Commit 9 — Billing preparation

**Commit message:** `feat: improve invoice workflow`

Zadaci:

- Dodati InvoiceLine API.
- Račun mora moći nastati iz appointmenta i service price.
- Dodati payment transactions.
- Dodati status:
  - draft
  - issued
  - cancelled
  - paid
  - partially_paid
  - refunded
- Dodati polja za hrvatski kontekst:
  - operator
  - payment_method
  - oib/vat_id
  - business_unit
  - register_id
  - fiscalization_status
  - fiscalization_reference optional
- Ne implementirati fiskalizaciju odmah, nego adapter interface.

Acceptance criteria:

- Iz termina se može generirati nacrt računa.
- Račun ima stavke.
- Plaćanje je zasebna transakcija, ne samo jedan string na računu.

---

## Commit 10 — Frontend inventory workflows

**Commit message:** `feat: add inventory operational screens`

Zadaci:

Dodati stranice:

- Inventory item detail
- Create/edit inventory item
- Batch list and batch detail
- Receive stock
- Transfer stock
- Write off stock
- Adjustment
- Service material templates
- Expiring batches
- Low stock alerts

Acceptance criteria:

- Korisnik može zaprimiti robu bez direktnog API poziva.
- Korisnik može prenijeti materijal iz glavnog skladišta u endoskopsku sobu.
- Korisnik može otpisati materijal s obaveznim razlogom.

---

## Commit 11 — Test suite

**Commit message:** `test: add backend and frontend test coverage`

Zadaci:

Backend testovi:

- auth login
- patients CRUD
- appointments overlap validation
- schedule/day
- FEFO consumption
- low stock
- expiring batches
- PO receiving
- audit logging
- RBAC denial cases

Frontend testovi:

- login screen smoke test
- dashboard smoke test
- inventory dashboard smoke test

Acceptance criteria:

- `make test` prolazi lokalno.
- FEFO test pokriva dvije serije s različitim rokovima.
- Appointment overlap test mora pasti ako se doda preklapajući termin.

---

## Commit 12 — OpenAPI cleanup and examples

**Commit message:** `docs: improve openapi examples and api documentation`

Zadaci:

- Dodati response_model za glavne endpointove.
- Dodati Pydantic output sheme.
- Dodati OpenAPI examples.
- Dodati curl primjere za:
  - login
  - create patient
  - create appointment
  - free slots
  - create inventory item
  - receive stock
  - complete appointment with consumption
  - create invoice

Acceptance criteria:

- `/docs` je dovoljno jasan da ga AI agent i developer mogu koristiti bez čitanja koda.

---

## Commit 13 — AI agent safe API

**Commit message:** `feat: add scoped ai agent api keys`

Zadaci:

- Dodati API key authentication.
- API key ima:
  - name
  - key_hash
  - scopes
  - active
  - last_used_at
  - expires_at
- AI endpointi prihvaćaju API key.
- AI agent smije:
  - pretražiti slobodne termine
  - kreirati pacijenta
  - kreirati termin
  - otkazati termin samo ako scope dopušta
- AI agent ne smije:
  - brisati podatke
  - mijenjati račune
  - raditi stock adjustment
  - čitati audit log

Acceptance criteria:

- API key s ograničenim scopeom ne može pozvati zabranjene endpointove.
- Sva AI aktivnost je auditirana.

---

## Commit 14 — Production deployment baseline

**Commit message:** `chore: add production deployment baseline`

Zadaci:

- Dodati production Dockerfile varijante.
- Dodati environment profiles:
  - local
  - staging
  - production
- Dodati backup skriptu za PostgreSQL.
- Dodati restore upute.
- Dodati primjer Google Cloud Run deployment dokumentacije.
- Dodati sigurnosne napomene za JWT_SECRET, CORS i HTTPS.

Acceptance criteria:

- Postoji realan put od lokalnog Docker Composea do Google Cloud deploymenta.
