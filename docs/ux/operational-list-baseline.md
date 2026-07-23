# Operativni popisi — početno stanje

Status: Faza A — izmjereno i dokumentirano, bez promjena korisničkog sučelja

Grana: `ux/information-architecture-simplification`

Polazište: `99802e0` (`Focus patient journey clinical context`)

Datum mjerenja: 23. 07. 2026.

Podaci: isključivo sintetički/demo podaci

## 1. Svrha i sigurnosne granice

Ova inventura prethodi pojednostavljenju popisa kliničkih dokumenata, računa i
evidencije aktivnosti. Za svaki podatak određuje treba li ga korisnik za
identifikaciju, odluku ili sljedeću radnju ili je tehnički, povijesni ili
provenance dokaz koji treba prikazati tek na zahtjev.

Faza A ne mijenja API-je, modele, autorizaciju, clinic/institution scope,
session ili CSRF zaštitu, audit redakciju, signed-report pravila ni mutacije.
Sakrivanje kontrole u sučelju nikada nije zamjena za backend autorizaciju.
Backend ostaje autoritativan, a PHI-safe audit DTO ostaje granica prikaza.

## 2. Metoda i dokaz

Baseline spaja pregled izvornog koda, pregled stvarnih mrežnih zahtjeva i
sintetički browser prolaz. Snimke su u ignoriranom direktoriju:

`.localrun/ux-operational-lists-phase-a/`

Za svaki od tri zaslona provjerene su dimenzije:

- `1440 × 900`
- `1280 × 800`
- `1024 × 768`

Snimke nisu commitane. Ne sadrže stvarne pacijente. Mrežne veličine su veličine
odgovora koje je browser prijavio u tom prolazu i ovise o sintetičkom skupu.
Zahtjev `/api/public-config` pripada shellu i odvojen je od request budgeta
samog popisa.

## 3. Klasifikacija sadržaja

| Oznaka | Značenje |
| --- | --- |
| `PRIMARY` | Potrebno za identifikaciju, sigurnu odluku ili sljedeću radnju. |
| `SECONDARY` | Korisno u retku, ali vizualno podređeno primarnom podatku. |
| `DETAIL-ONLY` | Potrebno tek nakon svjesnog otvaranja zapisa. |
| `ADVANCED-FILTER` | Koristan kriterij u rjeđem ili stručnom scenariju. |
| `ROLE-SPECIFIC` | Prikazuje se samo ulozi koja ga operativno koristi, uz backend provjeru. |
| `REDUNDANT` | Ponavlja drugi podatak ili ne pomaže odluci. |

## 4. Vizualni smjer zajedničkog obrasca

Zadržava se postojeći ASTRA dizajnerski sustav: Inter/system tipografija,
teal `#0f766e` za primarne radnje, slate za tekst, amber/crvena za upozorenja i
zelena za dovršeno. Ne uvodi se nova paleta ni UI framework.

```text
Naslov + kratka svrha                         [jedna globalna radnja]
[pretraga] [ključni filtri] [Napredni filtri]
─────────────────────────────────────────────────────────────────
identitet / predmet       jedan status       jedna primarna radnja
sekundarni kontekst                           [⋯ ostale radnje]
─────────────────────────────────────────────────────────────────
                          detalj tek na zahtjev
```

Prepoznatljivi obrazac je jedna kratka statusna rečenica po retku. Tehnički
badgeovi, ID-evi i provenance ne natječu se s operativnim statusom.

## 5. Klinički dokumenti — prije

Ruta: `/clinical-documents`

Primarna zadaća: prepoznati dokument, procijeniti treba li pregled i otvoriti
odgovarajući zapis.

| Mjera | Početno stanje |
| --- | --- |
| Mount requestovi zaslona | 2: `/api/patients?q=__no_patient__` i `/api/clinical-documents`; dodatni patient detail ako URL sadrži `patient_id` |
| Stupci | 8: Dokument, Pacijent, Datum, Tip, Izvor, Klasifikacija, Pregled, AI ekstrakcija |
| Statusi po retku | do 3 jednako naglašena: klasifikacija, pregled, AI |
| Stalni filtri | 4: tekst, sirovi Patient ID, tip, review status |
| CTA | 1 globalni; naslov dokumenta služi kao radnja retka |
| Detalj | zasebna ruta; pri mountu 4 requesta: dokument, audit, evidence timeline i addenda |
| Tehnički sadržaj | source type, record classification, AI status i raw patient ID fallback |
| 1024 px | osam stupaca ostaje u tablici; sadržaj s podacima može zahtijevati unutarnji horizontalni scroll |

Stvarni baseline zahtjevi:

- `/api/patients?q=__no_patient__`: `200`, 569 B
- `/api/clinical-documents`: `403`, 665 B za provjereni demo liječnički profil
- shell `/api/public-config`: `200`, 980 B

`403` je postojeće ograničenje dozvola ili demo fixturea, a ne stanje „nema
dokumenata”. Buduće sučelje mora razlikovati zabranu pristupa od praznog
rezultata. Faza A ga ne popravlja niti širi scope.

Klasifikacija:

| Podatak | Oznaka | Obrazloženje |
| --- | --- | --- |
| Pacijent, naslov, datum, tip | `PRIMARY` | Identifikacija dokumenta. |
| Jedan operativni status | `PRIMARY` | Odgovara treba li ljudska radnja. |
| Izvor, kada je rizičan ili nejasan | `SECONDARY` | Pomaže procjeni samo u iznimci. |
| Source type, AI faze, klasifikacija | `DETAIL-ONLY` | Tehnički/provenance dokaz. |
| Izvor, AI status, autor, raspon datuma | `ADVANCED-FILTER` | Nisu svakodnevni prvi kriteriji. |
| Sirovi Patient ID | `REDUNDANT` | Nije razumljiv operativni filter ni siguran fallback. |

### Ciljani after model

Najviše šest stupaca: Pacijent, Dokument, Datum, Tip, Status, Radnja. Stalni su
pretraga, patient autocomplete, tip i review status; ostalo je sklopljeno.
Detalj ostaje route detail i ne dohvaća se za neotvorene zapise.

## 6. Računi i plaćanja — prije

Ruta: `/invoices`

Primarna zadaća: prepoznati račun, vidjeti iznos i otvoreno dugovanje te
izabrati sljedeću financijsku radnju.

| Mjera | Početno stanje |
| --- | --- |
| Mount requestovi zaslona | 1: `/api/invoices` |
| Stupci | 5: Broj računa, Datum, Status, Plaćanje, Iznos |
| Statusi po retku | 2: invoice status i payment status |
| Filtri | 0 |
| CTA | broj računa otvara detalj; detalj zatim prikazuje više mutacijskih gumba |
| Detalj | prvi račun se automatski odabire; nema zasebnog detail requesta |
| Tehnički sadržaj | list DTO unaprijed sadrži `lines` i `payments` za svaki račun |
| 1024 px | prazna tablica nema page overflow; puni sadržaj i inline detalj nisu dokazani u baseline skupu |

Stvarni baseline zahtjevi za billing profil:

- `/api/invoices`: `200`, 569 B (prazan sintetički rezultat)
- shell `/api/public-config`: `200`, 980 B

Klasifikacija:

| Podatak | Oznaka | Obrazloženje |
| --- | --- | --- |
| Pacijent, datum, ukupni i otvoreni iznos | `PRIMARY` | Određuju identitet i obvezu. |
| Jedan operativni status | `PRIMARY` | Sažima nacrt, otvoreno, djelomično ili plaćeno. |
| Broj računa | `SECONDARY` | Koristan za referencu, ali ne zamjenjuje pacijenta. |
| Stavke, uplate, delivery history, provenance | `DETAIL-ONLY` | Potrebno nakon otvaranja računa. |
| Financijske mutacije | `ROLE-SPECIFIC` | Billing/reception prema backend ovlasti. |
| Odvojeni raw invoice/payment enum badgeovi | `REDUNDANT` | Jedan operativni status je jasniji. |

### Ciljani after model

Stupci: Pacijent, Datum, Iznos, Otvoreno, Status, Radnja. Payment history i
stavke ne smiju biti u list DTO-u ako mjerenje potvrdi stvarni payload trošak.
Jedna primarna radnja ovisi o statusu; ostalo je u meniju ili detalju.

## 7. Evidencija aktivnosti — prije

Ruta: `/audit-log`

Primarna zadaća: razumjeti tko je što učinio, nad kojim objektom, u kojem
scopeu i s kojim rezultatom.

| Mjera | Početno stanje |
| --- | --- |
| Mount requestovi zaslona | 1: `/api/audit-log` |
| Stupci | 5: Vrijeme, Radnja, Entitet, ID, Sažetak |
| Statusi po retku | nema jasnog operativnog statusa rezultata |
| Filtri | 0 |
| CTA | 0 |
| Detalj | ne postoji |
| Tehnički sadržaj | raw action, raw entity type i raw entity ID u glavnom retku |
| Visina retka | približno 48 px u izmjerenom skupu |
| 1024 px | stranica ne prelazi viewport; table wrapper ima oko 17 px unutarnjeg overflowa |

Stvarni baseline zahtjevi za administratorski profil:

- `/api/audit-log`: `200`, 10.947 B, 28 prikazanih redaka
- shell `/api/public-config`: `200`, 980 B

Otvaranje evidencije samo stvara događaj `audit_log.viewed`, pa lista u
baselineu sadrži ponavljajuće tehničke događaje. Backend već vraća PHI-safe
`ClinicAuditEventOut`; raw before/after snapshotovi, klinički tekst, tokeni,
cookieji i request body nisu dio DTO-a i ne smiju postati dio budućeg drawera.

Klasifikacija:

| Podatak | Oznaka | Obrazloženje |
| --- | --- | --- |
| Vrijeme, korisnik, razumljiva radnja, objekt, scope, rezultat | `PRIMARY` | Potpuni operativni sažetak događaja. |
| Tehnički event type, object ID, request/correlation ID | `DETAIL-ONLY` | Potrebno za istragu, ne za skeniranje liste. |
| Reason code i changed field names | `DETAIL-ONLY` | Sigurni tehnički dokaz bez vrijednosti polja. |
| Scope i security classification filtri | `ADVANCED-FILTER` | Samo ovlaštenim ulogama. |
| Globalni security audit | `ROLE-SPECIFIC` | Ne smije se izvesti iz clinic operational scopea. |
| Raw entity ID kao primarni stupac | `REDUNDANT` | Ne pomaže svakodnevnom razumijevanju. |

### Ciljani after model

Stupci: Vrijeme, Korisnik, Radnja, Objekt, Scope, Rezultat. Tehnički detalj je
read-only drawer s focus trapom, Escape zatvaranjem i povratom fokusa. Drawer
koristi postojeći PHI-safe DTO i ne uvodi raw snapshot podatke.

## 8. Mrežni baseline po radnji

| Zaslon | Početno otvaranje | Promjena filtra | Otvaranje detalja | Nakon mutacije | Eager detalji |
| --- | --- | --- | --- | --- | --- |
| Dokumenti | patient dummy search + document list | document list se ponovno dohvaća; autocomplete tek od 2 znaka; `useApi` prekida stari request | detail ruta šalje 4 requesta | ovisi o detail workflowu | list vraća puni dokument DTO |
| Računi | invoice list | nema filtera | nema requesta jer je detalj u list DTO-u i prvi red auto-selected | POST pa GET zahvaćenog računa | lines i payments svih računa |
| Audit | audit list | nema filtera | nema detalja | nema mutacije | nema dodatnih requestova; list je PHI-safe |

Dokument dummy pretraga na mountu i eager invoice lines/payments kandidati su
za optimizaciju, ali promjena je dopuštena tek nakon mjerenja nepraznog
sintetičkog skupa. Ne stvaraju se novi endpointi samo zato što UI skriva
stupce.

## 9. Nalazi i odbijene prečice

1. Pojednostavljenje ne smije biti samo CSS skrivanje: list DTO i request
   ponašanje moraju odgovarati stvarnoj granici list/detail.
2. Prazan rezultat i `403` moraju imati različite poruke.
3. Dokument list trenutno daje jednaku važnost trima statusima.
4. Račun nema pacijenta kao primarni identitet, a detalj i payment history su
   eager u listi.
5. Audit prikazuje tehničke nazive, ali već ima sigurnu DTO granicu koju treba
   očuvati.
6. Ne uvodi se univerzalna konfiguracijska tablica s desecima propova.
7. Ne mijenja se backend scope kako bi demo profil dobio širi pristup.
8. Ne uklanjaju se audit, provenance ili signed-report podaci iz modela.

## 10. Faza A — izlazni kriterij

- before i ciljani after model dokumentirani su za sva tri zaslona;
- snimke za tri tražene širine postoje u ignoriranom direktoriju;
- stvarni requestovi i veličine odgovora zabilježeni su;
- sigurnosne granice i postojeći `403` jasno su navedeni;
- Faza A ne tvrdi da su Faze B–G implementirane ili validirane.
