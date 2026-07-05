# ASTRA Clinic Core — kritički osvrt v8

Datum pregleda: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## Sažetak

Codex je implementirao velik dio v7 smjera. Projekt je sada realno u fazi **demo/pilot readiness**, ali još uvijek isključivo s demo podacima.

Potvrđeno je da sada postoje:

- `AppointmentDetail` stranica.
- Materijalni workflow na appointment detailu.
- Povezani račun iz appointment detaila.
- Stock movements povezani s appointmentom.
- Audit timeline komponenta.
- Entity-level audit filtering po `entity_type` i `entity_id`.
- Pilot demo smoke test koji prolazi kroz appointment -> material consumption -> invoice -> payment -> purchase receive -> audit.
- Demo seed command.
- Demo reset command s production guardom.
- Pilot runbook.
- Data-only module manifest loader.
- Gastroenterology service manifest.

Moj stav: **v7 je vrlo dobar. ASTRA sada ima prvi smisleni end-to-end demo flow.**

Ali to još uvijek nije spremno za stvarne pacijente. Sljedeći sprint mora biti **Controlled Pilot Hardening Sprint**: ne dodavati nove velike module, nego učiniti demo/pilot robustnim, razumljivim i sigurnim za zatvorenu prezentaciju ili interni test.

## Što je dobro

### 1. Appointment detail je jako važan dodatak

`frontend/src/pages/AppointmentDetail.tsx` sada prikazuje:

- podatke termina
- pacijenta
- uslugu
- liječnika
- sobu
- status
- napomenu
- materijalni workflow
- povezani račun
- kretanja zalihe vezana uz termin
- audit timeline

To je pravi smjer. Dashboard ostaje cockpit, a appointment detail postaje radna površina za pojedini slučaj.

### 2. Materijalni workflow je sada bolji nego prije

Appointment detail:

- učitava material suggestions
- popunjava auto-consumable stavke
- detektira missing required variable material
- detektira prekoračenje dostupne zalihe
- traži potvrdu prije skidanja zalihe
- zove `complete-with-consumption`

To je dovoljno za demo i zatvoreni pilot s demo podacima.

### 3. Pilot smoke test postoji

`backend/tests/integration/test_pilot_demo_flow.py` prolazi kroz ključni flow:

- kreira korisnika s permissionima
- seed-a patient/provider/room/service
- kreira inventory item i batch
- dodaje service material template
- kreira appointment
- završava appointment s potrošnjom materijala
- provjerava smanjenje zalihe
- kreira draft invoice
- izdaje invoice
- provjerava noop fiscalization
- evidentira payment
- kreira supplier/PO/line
- zaprima PO line
- provjerava povećanje zalihe
- provjerava audit log request_id

Ovo je izuzetno važan test jer dokazuje cijeli operativni lanac.

### 4. Demo seed/reset postoji

`app.demo.seed` stvara demo korisnike, pacijenta, liječnika, sobu, uslugu, skladište, artikl, batch, service material template, appointment i purchase order.

`app.demo.reset` odbija raditi u production modu. To je točno.

### 5. Pilot runbook postoji

`docs/PILOT_RUNBOOK.md` daje:

- kako startati demo
- kako seedati podatke
- demo login podatke
- demo script
- očekivane ishode
- poznata ograničenja
- backup reminder

To je odličan korak prema stvarnom demonstriranju aplikacije.

### 6. Module manifest loader postoji

`backend/app/modules/manifest.py` sada ima data-only loader za:

- Module manifest
- Services
- Material templates

Ima idempotentni pristup po `Module.key`, `Service.code` i kombinaciji `service_id + inventory_item_id` za material template.

To je upravo smjer koji treba: konfiguracijska modularnost, bez izvršavanja proizvoljnog plugin koda.

## Preostale slabosti

### 1. Module loader treba testove i bolju validaciju

Nisam našao jasan test za module manifest loader. Treba testirati:

- load module once
- load module twice without duplicates
- update service fields by code
- material template import by service code + item SKU
- missing inventory item should not crash, but should log/report warning
- invalid manifest should fail jasno

Sada loader postoji, ali bez testova može tiho proizvoditi krivi katalog.

### 2. Pilot smoke test je odličan, ali treba biti stabilniji

Pilot smoke test koristi fiksni datum `2026-07-05`. To je u ovom kontekstu aktualan datum, ali dugoročno je bolje koristiti `date.today()` ili helper. Demo flow mora ostati živ i za mjesec dana.

Također, payment u testu šalje `100`, a service price može postati drugačiji ako se promijeni fixture. Bolje je čitati remaining amount iz invoicea.

### 3. Appointment detail radi, ali treba bolju UX zaštitu

Materijalni panel treba dodatno prikazati:

- kategoriju: obavezno / opcionalno / varijabilno
- dostupnu zalihu i jedinicu mjere
- default quantity
- warning ako je stock ispod reorder pointa nakon potrošnje
- jasnu razliku između “učitaj prijedlog” i “potvrdi završetak”

Sada je dobro za demo, ali još nije dovoljno za nekoga tko nije sudjelovao u razvoju.

### 4. Purchase receiving UI treba još zaštite

Postoji workflow, ali treba potvrditi:

- frontend blokira over-receive
- LOT/expiration je obavezan u UI kad backend zna da je tracking enabled
- default lokacija je jasna
- nakon receivea se refreshaju order, inventory i low-stock status

Za zatvoreni pilot mora biti teško napraviti glupu grešku.

### 5. API key management treba policy sloj

UI postoji, ali treba bolji scope policy:

- read-only
- AI safe
- operational write
- dangerous

Dangerous scopeovi trebaju potvrdu i upozorenje.

AI agent ne smije dobivati inventory.adjust, inventory.write_off, billing.mark_paid ili audit.read bez eksplicitnog razloga.

### 6. Audit timeline je dobar početak, ali treba čitljiviji prikaz

`AuditTimeline` prikazuje action, entity_type, timestamp, actor_type, summary i request_id. To je dobro, ali za demo/pilot treba bolje:

- actor ime ili API key name ako je dostupno
- before/after diff za update
- human-readable labels
- filteri po akciji

Audit nije samo log; to je dokaz povjerenja.

### 7. Nema jasnog pilot feedback mehanizma

Ako se radi zatvoreni pilot, treba imati način prikupljanja feedbacka:

- što je radilo
- gdje je korisnik zapeo
- gdje je UI nejasan
- koji backend errori su se pojavili
- što nedostaje za stvarni rad

To može biti dokument, GitHub issue template ili jednostavan feedback form.

### 8. Nije spremno za stvarne pacijente

Unatoč napretku, projekt još nema:

- formalni GDPR DPIA
- upravljanje korisnicima u punom smislu
- password reset
- access logging za čitanje pacijentovih podataka
- retention policy
- realnu fiskalizaciju
- produkcijsko promatranje/monitoring
- backup restore test automatizaciju

Zato je maksimalno dopušteno: **zatvoreni demo/pilot s demo podacima**.

## Ocjena nakon v7

### Backend

Dobar za demo i pilot s demo podacima.

### Frontend

Prvi put stvarno operativan.

### Testovi

Dobar napredak zbog pilot smoke testa, ali treba testirati loader i UI/e2e stabilnost.

### Modularnost

Sada postoji stvarni početak loadera.

### Sigurnost

Dobra za demo; nedovoljna za realne pacijente.

### Produktna zrelost

Demo-ready: da.
Production-ready: ne.

## Preporučeni sljedeći sprint

Naziv:

**Controlled Pilot Hardening Sprint**

Cilj:

Pripremiti ASTRA Clinic Core za zatvorenu demonstraciju ili interni pilot s demo podacima, s minimalnim rizikom i jasnim povratnim informacijama.

Prioriteti:

1. Testirati module manifest loader.
2. Učiniti pilot smoke test dinamičnim i stabilnim.
3. Dodati Playwright ili minimalni frontend smoke test za demo flow.
4. Doraditi material consumption UX.
5. Doraditi purchase receiving UX.
6. Doraditi invoice/payment UX.
7. Harden API key scope UI.
8. Poboljšati audit timeline čitljivost.
9. Dodati pilot feedback template.
10. Dodati “real data readiness checklist” koja eksplicitno blokira stvarne pacijente.

## Zaključak

V7 je jedan od najboljih skokova dosad. ASTRA sada ima demonstrabilan operativni lanac. To je velika stvar.

Moj čvrst stav: **nemoj sada krenuti u nove medicinske module.** Prvo napravi jedan zatvoreni demo koji se može pokazati bez srama, s jasnim flowom i demo podacima. Kad taj pilot bude stabilan, tek tada ima smisla graditi Gastroenterology module v1, AI recepcionara ili integracije s Google Calendarom/OpenEMR-om.
