# ASTRA kanonska terminologija i safety microcopy

Status: Faza B — kanonski korisnički pojmovi

Datum: 23. 07. 2026.

Opseg: korisničko sučelje; API polja, enum vrijednosti, klase i rute ostaju
nepromijenjeni.

## 1. Načela

- Standardni UI koristi hrvatski, a interni tehnički naziv ostaje u kodu.
- Jedan pojam ima jedno značenje u cijeloj aplikaciji.
- Klinički izvedeni podatak nikada se jezikom ne izjednačava s izvornim
  dokumentom ili potvrđenom kliničkom činjenicom.
- „AI skica” opisuje nepotvrđeni sadržaj; „pregledani sažetak” sadržaj koji je
  prošao dopuštenu ljudsku provjeru.
- „Povezano s izvorom” opisuje vezu/provenance; ne tvrdi da je sadržaj točan,
  pregledan ili klinički potvrđen.
- Sigurnosna poruka objašnjava granicu jednom, a ne u nizu ponovljenih
  paragrafa.

## 2. Terminološka mapa

| Interni pojam | Dosadašnja UI oznaka | Kanonska hrvatska oznaka | Kratka pomoć / definicija | Ciljne uloge |
| --- | --- | --- | --- | --- |
| `PatientJourney` | Patient Journey, putovanje, tijek pacijenta | **Tijek dolaska pacijenta**; u dnevnom zbroju **dolazak** | Jedan fizički dolazak koji povezuje pripremu, prijem, aktivnosti, račun i završetak. | sve operativne |
| `JourneyActivity` | activity, aktivnost, primary | **Aktivnost dolaska** | Jedna usluga, pregled ili postupak unutar istog fizičkog dolaska. | liječnik, sestra/tehničar, recepcija, naplata |
| `ClinicalEpisode` | Episode, epizoda | **Klinička epizoda** | Stručni klinički kontekst kroz vrijeme; nije isto što i jedan termin ili dolazak. | liječnik, pregledavatelj dokumenata |
| `ClinicalPlan` | Clinical Plan | **Klinički plan** | Strukturirani plan koji postaje služben tek nakon dopuštene ljudske potvrde. | liječnik |
| `ClinicalFinding` | finding, source-linked finding | **Nalaz povezan s izvorom** | Izdvojena informacija s vezom na izvor; sama po sebi nije dijagnoza. | liječnik, pregledavatelj dokumenata |
| `Evidence` | evidence, dokaz | **Izvor / izvorni zapis** | Dokument ili zapis iz kojeg je izvedena tvrdnja. „Dokaz” se koristi samo kada je kliničko značenje doista dokazno. | liječnik, pregledavatelj dokumenata |
| `EvidenceTimeline` | evidence timeline, timeline | **Klinička vremenska crta** | Kronološki prikaz događaja s poveznicama na izvore. | liječnik, pregledavatelj dokumenata |
| `ClinicalSummary` | Clinical Summary, sažetak | **Sažetak pacijenta** | Pomoćni, izvorima povezani pregled relevantnih činjenica; prikazuje status pregleda i zastarjelost. | liječnik |
| `Readiness` | readiness | **Spremnost sustava** za administratorski alat; **potrebna provjera** za klinički signal | Administratorska spremnost nije isto što i kliničko odobrenje postupka. | administrator; liječnik za klinički signal |
| `Workflow` | workflow, radni tok | **Tijek rada**; na popisu **Zadaci** | Operativni slijed i odgovornost; nije klinička odluka. | sve operativne |
| `source-linked` | source-linked | **povezano s izvorom** | Tvrdnja ili događaj ima vidljivu referencu na izvorni zapis. | liječnik, pregledavatelj dokumenata |
| `AI draft` | AI draft | **AI skica** | Strojno generirani prijedlog koji nije pregledani sažetak, nalaz ili odluka. | liječnik, pregledavatelj dokumenata |
| `DocumentReview` | document review | **pregled dokumenta** / **liječnički pregled dokumenta** | Evidentira pregled izvora u skladu s dopuštenjem; ne donosi odluku automatski. | liječnik, pregledavatelj dokumenata |
| `Blocker` | blocker, blokator | **problem koji zaustavlja radnju**; kratko **blokada** | Stanje zbog kojeg se određena administrativna ili klinička radnja ne može nastaviti bez ovlaštene odluke. | sve operativne |
| `ClinicalProvenance` | provenance | **podrijetlo kliničkog podatka** | Tko, kada, u kojoj ustanovi i iz kojeg izvora je zapis nastao. | liječnik, pregledavatelj, auditor |
| `Patient Workspace` | Patient Workspace | **Karton pacijenta** | Ulaz u podatke i radnje vezane uz jednog pacijenta. | sve ovlaštene pacijentske uloge |
| `read-only` | read-only | **samo za čitanje** | Podatak se može pregledati, ali ne i mijenjati u tom prikazu. | sve |
| `snapshot` | snapshot | **snimka stanja** | Nepromjenjivi zapis stanja u određenom trenutku; nije kliničko odobrenje. | liječnik, administrator |

## 3. Standard sigurnosnih poruka

### 3.1 Globalna napomena izvedenih kliničkih podataka

Komponenta: `ClinicalDerivedDataNotice`

> AI i drugi izvedeni podaci nisu dijagnoza ni izvor istine. Provjerite
> povezani izvorni dokument; liječnički pregled ostaje obvezan. Ovaj prikaz sam
> ne mijenja status, ne stvara zadatak i ne šalje poruku.

Prikazuje se jednom po relevantnom kliničkom području. Ima semantičku oznaku
`role="note"` i razumljiv `aria-label`, ali nema `aria-live`, kako ponovljeno
renderiranje ne bi stvaralo buku čitaču zaslona.

### 3.2 Kontekstualno upozorenje

Prikazuje se samo kada konkretno stanje zahtijeva pažnju, primjerice:

- sažetak je zastario;
- izvor nije pregledan;
- dokument nema dovoljnu referencu;
- korisnik nema dopuštenje za taj sloj;
- klinička provjera još nije donesena.

Poruka mora navesti što se dogodilo i što korisnik može učiniti. Ne ponavlja
cijelu globalnu sigurnosnu napomenu.

### 3.3 Pomoć uz polje

`HelpHint` ili opis vezan uz konkretno polje objašnjava format, izvor ili
posljedicu unosa. Ne koristi se za ponavljanje opće kliničke granice.

## 4. Prije / poslije

| Prije | Poslije |
| --- | --- |
| „Patient Workspace” | „Karton pacijenta” |
| „AI draft” | „AI skica” |
| „source-linked finding zapis” | „nalaz povezan s izvorom” |
| „source-linked timeline događaj” | „događaj povezan s izvorom” |
| „Read-only zapis” | „Samo za čitanje” |
| četiri odvojena paragrafa o tome što prikaz nije | jedna dostupna `ClinicalDerivedDataNotice` napomena |
| tehnički `knowledge impact` | „doprinos pregledanom kliničkom znanju” |
| neujednačeni `Ceka`, `Klinicki`, `Sazetak`, `lijecnik`, `paznja` | „Čeka”, „Klinički”, „Sažetak”, „liječnik”, „pažnja” |

## 5. Sigurnosna provjera

- Promijenjene su samo korisničke oznake i prezentacija safety teksta.
- API putanje, request/response polja, enum vrijednosti i autorizacija nisu
  mijenjani.
- `ClinicalDerivedDataNotice` ne mijenja stanje i nema mrežnih poziva.
- Izvorni dokument i status liječničkog pregleda ostaju eksplicitni.
- Skrivena ili konsolidirana poruka nije zamjena za backend gate.
