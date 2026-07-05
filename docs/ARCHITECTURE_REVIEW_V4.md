# ASTRA Clinic Core — kritički osvrt v4

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Projekt je nakon v3 prompta ponovno napredovao. Vidljiv je pomak iz “endpoint-heavy” MVP-a prema ozbiljnijoj arhitekturi sa service layerom.

Najvažnije promjene koje su sada vidljive:

- postoji `backend/app/services/billing.py`
- postoji `backend/app/services/procurement.py`
- billing logika je izvučena u funkcije kao što su `draft_invoice_from_appointment`, `issue_invoice`, `record_payment`, `mark_invoice_paid`
- procurement receiving logika je izvučena u `receive_purchase_order`
- dodan je `InvoiceNumberSequence`
- draft račun sada dobiva `DRAFT-...` broj, a službeni broj tek pri izdavanju
- issue invoice koristi zaključavanje sequence retka preko `with_for_update()`
- invoice line editing je blokiran izvan draft statusa
- payment overpay je blokiran
- required variable material sada mora imati unesenu količinu prije completiona

To je vrlo dobar pomak. Projekt sada sve više sliči na ozbiljan clinic operations core, a ne samo na brzinski CRUD.

Međutim, sada je potpuno jasno da sljedeći sprint više ne smije dodavati poslovne funkcije. Mora dokazati ispravnost. Bez testova i CI-ja, svaka sljedeća iteracija može nehotice slomiti inventar, račune ili audit.

## Što je sada dobro

### 1. Billing service layer je dobar iskorak

`billing.py` sada sadrži centralne funkcije:

- `calculate_line_total`
- `recalculate_invoice_total`
- `ensure_invoice_editable`
- `ensure_invoice_payable`
- `next_invoice_number`
- `draft_invoice_number`
- `draft_invoice_from_appointment`
- `issue_invoice`
- `add_invoice_line`
- `update_invoice_line`
- `delete_invoice_line`
- `record_payment`
- `mark_invoice_paid`

To je pravi smjer. Endpointi više ne bi trebali nositi svu poslovnu logiku.

### 2. Invoice numbering je bitno sigurniji

Prethodna logika temeljena na zadnjem ID-u bila je rizična. Sada postoji `InvoiceNumberSequence`, a `next_invoice_number` zaključava sequence redak. To je znatno bolje.

Dobra odluka je i to da draft invoice dobiva privremeni `DRAFT-...` broj, a službeni broj se dodjeljuje tek kod izdavanja.

### 3. Invoice status workflow je počeo dobivati oblik

`ensure_invoice_editable` dopušta izmjenu stavki samo na draft računu. To je vrlo važno. Nakon izdavanja računa ne smije se slobodno mijenjati sadržaj bez korekcijskog/storno workflowa.

`ensure_invoice_payable` blokira plaćanje cancelled računa.

### 4. Payment overpay je blokiran

`record_payment` provjerava prelazi li uplata ukupni iznos računa. To je ispravna MVP politika. Kasnije se može dodati preplata kao poseban koncept, ali nije dobra ideja sada.

### 5. Procurement service layer je uveden

`procurement.py` sada centralizira:

- izračun linije
- recalculation total amount
- derive purchase order status
- receive purchase order

To je dobar smjer jer receiving nije trivijalan CRUD.

### 6. Material consumption semantics su bolji

Kod sada blokira completion ako postoji obavezni varijabilni materijal bez unesene količine. To je važno za stvari poput propofola ili drugih potrošnih materijala koji se ne smiju naslijepo skidati kao fiksna količina.

## Kritične rupe koje ostaju

### 1. I dalje nema vidljivog test suitea

Pretraživanje repozitorija ne pokazuje test infrastrukturu. Ovo je sada najveći tehnički rizik.

Kod već sadrži dovoljno poslovne logike da ručno testiranje nije dovoljno. Trebaju pytest testovi za:

- permissions
- appointment conflict
- FEFO
- rollback potrošnje materijala
- PO partial receive
- invoice issue numbering
- payment partial/full
- audit before/after
- API key scopes

Bez toga projekt ne smije ići u daljnje širenje.

### 2. Nema vidljivog CI-ja

Nema dokaza da svaki push pokreće:

- backend testove
- frontend build
- type/lint check
- migracije na praznoj bazi

Za projekt koji se gradi uz Codex, CI je obavezan. AI vrlo lako popravi jednu stvar i pokvari drugu.

### 3. Transaction boundary još treba dokazati

Service layer je dobar, ali treba testirati atomicity.

Kritični scenariji:

- appointment completion troši dva materijala; drugi nema zalihu; prvi se ne smije skinuti
- PO receive ima dvije linije; druga prelazi naručenu količinu; prva ne smije ostati zaprimljena
- payment creation pukne nakon promjene invoice statusa; status ne smije ostati polovičan

Ako testovi ne potvrde rollback, sustav nije spreman za stvarne podatke.

### 4. `record_payment` može imati relationship/double-count rizik

`record_payment` kreira `PaymentTransaction`, append-a ga u `invoice.payments`, zatim recalculira total kroz relationship kolekciju.

To može biti u redu, ali mora biti testirano. Posebno treba provjeriti:

- partial payment 50 na invoice 100 daje `partially_paid`
- dodatnih 50 daje `paid`
- `mark_invoice_paid` nakon toga ne kreira duplu uplatu
- API response ne prikazuje duplicirane payments u istoj session kolekciji

### 5. `issue_invoice` nema jasno zaključavanje cijelog invoice workflowa

`issue_invoice` dodjeljuje broj i status `issued`, ali treba testirati i osigurati:

- invoice mora imati barem jednu stavku
- total_amount mora biti > 0 ili policy jasno dopušta 0
- invoice lines se nakon issue ne mogu dodavati/mijenjati/brisati
- payment se smije dodati samo na issued/partially_paid, ne na draft ako tako odlučimo

Trenutno `ensure_invoice_payable` blokira samo cancelled. Treba odlučiti smije li se plaćati draft. Moj stav: **ne smije**. Prvo issue, onda payment.

### 6. `update_invoice` endpoint je preširok

Generic PATCH na invoice može mijenjati širok skup polja. To je opasno nakon issue.

Treba ograničiti:

- draft: dopuštene administrativne izmjene
- issued: samo vrlo ograničena polja, npr. notes ili fiscalization metadata
- paid/cancelled: gotovo ništa bez posebnog workflowa

### 7. `create_invoice` s korisničkim invoice_number je rizičan

Endpoint dopušta payload invoice number ili generira draft. Za sigurnost je bolje:

- ignorirati korisnički invoice_number za draft
- uvijek generirati `DRAFT-...`
- službeni broj samo preko `/issue`

Inače vanjski API ili korisnik može slučajno napraviti nered u numeraciji.

### 8. Procurement receiving treba rollback test i možda service-level snapshots

`receive_purchase_order` sada vraća tuple `(line, batch, movement)`, što je dobro za audit. Ali treba osigurati da se audit radi tek nakon svih validacija ili da rollback briše i audit ako nešto pukne.

Preporuka:

- prvo validirati sve receive lines
- zatim primijeniti promjene
- zatim auditirati

Tako se smanjuje rizik polovičnih promjena.

### 9. Nedostaje modularni documentation layer

Projekt ima arhitektonske review dokumente i Codex promptove, ali treba dokumente koji su direktno operativni:

- `docs/TESTING.md`
- `docs/SECURITY_MODEL.md`
- `docs/INVENTORY_LEDGER.md`
- `docs/BILLING_WORKFLOW.md`
- `docs/PROCUREMENT_WORKFLOW.md`

### 10. README i SECURITY još trebaju produkcijsko upozorenje

README i dalje ima dev credentiale. To je OK, ali mora biti jasno označeno kao development-only. Treba dodati `SECURITY.md` i compliance disclaimere.

## Moj stav o prioritetu

Sada više ne bih radio nove funkcije. Ne bih radio Google Calendar. Ne bih radio fiskalizaciju. Ne bih radio nove medicinske module.

Sljedeći sprint mora biti:

1. pytest infrastruktura
2. business-rule testovi
3. CI pipeline
4. transaction rollback testovi
5. invoice status/issue/payment policy
6. security/compliance docs

Tek nakon toga ima smisla razvijati frontend workflowe, integracije, module i fiskalizaciju.

## Zaključak

Projekt je došao do vrlo dobre razvojne točke. Sada ima core scheduling, inventory, procurement i billing arhitekturu koja ima smisla.

Najveća opasnost sada je lažni osjećaj sigurnosti: kod izgleda zrelo, ali bez testova i CI-ja nije dokazano zreo.

Moj čvrst zaključak: **ASTRA Clinic Core sada treba postati test-driven i transaction-safe prije bilo kakvog daljnjeg širenja.**
