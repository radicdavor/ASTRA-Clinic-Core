# ASTRA UX i sadržajna inventura — postojeće stanje

Status: Faza A — dokumentirano postojeće stanje, bez promjena korisničkog sučelja

Grana: `ux/information-architecture-simplification`

Polazište: `29114fa` (`Isolate Playwright development server`)

Datum inventure: 23. 07. 2026.

Podaci: isključivo sintetički/demo podaci

## 1. Svrha i granice

Ovaj dokument je kontrolna točka prije pojednostavljenja informacijske
arhitekture. Cilj nije vizualno redizajnirati ASTRA-u niti ukloniti postojeće
funkcije, nego utvrditi:

- koja je primarna zadaća svakog zaslona;
- što pojedina uloga treba vidjeti odmah;
- što se može premjestiti u sekundarni ili napredni prikaz;
- gdje isti podatak ili navigacijski pojam postoji više puta;
- gdje broj zahtjeva, kontrola i sekcija povećava vrijeme snalaženja;
- koje sigurnosne i kliničke granice svaka buduća promjena mora sačuvati.

Faza A ne mijenja rute, API-je, autorizaciju, audit, kliničke podatke ni
potpisane nalaze. Brojevi klikova u scenarijima procjene su iz pregleda izvornog
koda i sintetičkog prolaza. Ljudska evaluacija upotrebljivosti tek slijedi.

## 2. Metoda

Inventura kombinira četiri izvora:

1. statički pregled svih ruta, `AppShell` navigacije i mount-time API poziva;
2. pregled uloga i dopuštenja prikazanih u sučelju;
3. sintetičke prolaze kroz najčešće zadatke;
4. snimke osam reprezentativnih zaslona u četiri veličine prikaza.

Snimke i strojno očitana mjerenja nalaze se u ignoriranom privremenom
direktoriju:

`.localrun/ux-baseline-phase-a/`

Snimke nisu dio repozitorija jer sadrže prolazno stanje demo okruženja. Svih 32
datoteka provjereno je na stvarne dimenzije:

- `1440 × 900`
- `1280 × 800`
- `1024 × 768`
- `768 × 1024`

## 3. Klasifikacija sadržaja

| Oznaka | Značenje |
| --- | --- |
| `ESSENTIAL` | Nužno za primarnu zadaću na trenutnom zaslonu. |
| `CONTEXTUAL` | Korisno za odluku, ali ne mora uvijek biti otvoreno. |
| `ADVANCED` | Potrebno manjem broju korisnika ili u rjeđem scenariju. |
| `REDUNDANT` | Ponavlja već vidljivu informaciju ili radnju. |
| `HISTORICAL` | Važno za trag i retrospektivu, ali ne za trenutačnu radnju. |
| `TECHNICAL-ONLY` | Tehnički/statusni detalj namijenjen podršci ili administratoru. |

## 4. Trenutačni navigacijski model

### 4.1 Primarna navigacija

- Danas
- Pacijenti
- Naručivanje
- Znanje

### 4.2 Sekundarna navigacija pod jednim pojmom „Više”

- Klinički alati: Dokumenti, Laboratorij, Terapije, Gastroenterologija
- Organizacija rada: Prijem, Zadaci
- Nabava i zalihe: Inventar, Dobavljači, Narudžbenice
- Financije: Računi
- Administracija: Usluge, Klinike i osoblje, Moduli, Evidencija aktivnosti,
  API ključevi, Spremnost sustava
- Demo alati za administratora

Glavni problem nije broj funkcija nego to što jedan generički pojam „Više”
skriva šest različitih mentalnih modela. Korisnik mora otvoriti izbornik prije
nego može procijeniti gdje se funkcija nalazi.

`AppShell` dohvaća javnu konfiguraciju i popis klinika. U zaglavlju se prikazuje
„Administratorski prikaz” ili „Operativni prikaz”, ali nije dovoljno jasno koja
je aktivna uloga, koje su joj odgovornosti i zašto pojedine stavke nisu
prikazane. Promjena klinike trenutno ponovno učitava aplikaciju bez vidljive
provjere nespremljene skice.

## 5. Potpuna inventura ruta

Broj API poziva je statički broj deklariranih `useApi` poziva u komponenti, a
ne nužno broj svakog mrežnog zahtjeva u svim stanjima. Dva shell zahtjeva nisu
ponovljena u svakoj stavci.

### 5.1 Operativne i pacijentske rute

| Ruta | Zaslon | Primarna svrha i radnja | Uloge | API deklaracije | Vidljivi sadržaj / klasifikacija | Nalaz |
| --- | --- | --- | --- | ---: | --- | --- |
| `/` | `DailyClinicDashboard` | Uočiti sljedećeg pacijenta/problem i otvoriti jednu sljedeću radnju. | administrator, liječnik, sestra/tehničar, recepcija, naplata, pregledavatelj dokumenata | 4 | vrijeme, pacijent, aktivnosti, status, problem, primarna radnja — `ESSENTIAL`; dodatni filtri — `CONTEXTUAL` | Najbolji postojeći model prioriteta; zadržati jednu glavnu radnju. |
| `/patients` | `Patients` | Pronaći pacijenta i otvoriti karton ili dodati pacijenta. | operativne kliničke uloge | 1 | pretraga i rezultat — `ESSENTIAL` | Jednostavan ulaz; treba jasno razlikovati pretragu od dodavanja. |
| `/patients/new` | `PatientForm` | Unijeti osnovne podatke novog pacijenta. | ovlaštene operativne uloge | 0 | identitet i kontakt — `ESSENTIAL`; napomena — `CONTEXTUAL` | Dobar mali obrazac; pomoć ne smije prekidati unos. |
| `/patients/:id` | `PatientDetail` | Razumjeti pacijenta i pokrenuti sljedeću pacijentsku radnju. | ovlaštene kliničke/operativne uloge | 11 | identitet i sljedeći termin — `ESSENTIAL`; dokumenti/termini/lab./terapije — `CONTEXTUAL`; zbrojevi i audit — `HISTORICAL`; dupli metrički blokovi — `REDUNDANT` | Najveći sadržajni problem: 25 gumba, 14 kartica, 28 naslova, 11 tabova i 3263 px visine. |
| `/reception` | `Reception` | Prijaviti dolazak i obaviti prijem. | recepcija, sestra/tehničar, administrator | 6 | radni red i prijem — `ESSENTIAL`; detalji provjera — `CONTEXTUAL` | Funkcija se preklapa s dashboard-native prijemom; treba jedan kanonski ulaz. |
| `/appointments` | `Appointments` | Pregledati termine i otvoriti novi/postojeći termin. | recepcija, kliničke uloge, administrator | 1 | popis, datum i status — `ESSENTIAL` | Termin je operativna lista; ne smije postati drugi dnevni dashboard. |
| `/appointments/new` | `AppointmentForm` | Naručiti pacijenta na jednu uslugu i spriječiti konflikt. | recepcija, sestra/tehničar, liječnik, administrator | 6 | pacijent, klinika, usluga, liječnik, prostorija, datum/vrijeme — `ESSENTIAL`; tehnički detalji dostupnosti — `CONTEXTUAL` | Šest izvora na mountu povećava ovisnost; hijerarhija obrasca je prihvatljiva. |
| `/appointments/package` | `PackageBooking` | Naručiti povezani paket aktivnosti kao jedan dolazak. | ovlaštene uloge za naručivanje | 5 | paket, redoslijed, resursi, preview — `ESSENTIAL`; detalji konflikta — `CONTEXTUAL` | Napredan scenarij treba ostati odvojen od brzog pojedinačnog termina. |
| `/appointments/:id` | `AppointmentDetail` | Razumjeti i promijeniti jedan termin. | ovlaštene operativne uloge | 5 | termin i radnje — `ESSENTIAL`; povijest/provenance — `HISTORICAL` | Sedam izvornih gumba upućuje na previše istovrijednih radnji. |
| `/journeys/:id` | `PatientJourneyWorkspace` | Izvesti cijeli operativni tijek jednog fizičkog dolaska. | recepcija, liječnik, sestra/tehničar, naplata, administrator | 15 | pacijent, aktivnosti, trenutačna faza, sljedeća radnja — `ESSENTIAL`; dokumenti/priprema/check-in/pregled/naplata — `CONTEXTUAL`; timeline/AI sažetak — `ADVANCED` | 15 API deklaracija i 15 gumba; učitava timeline/sažetak i kad nisu trenutni posao. |
| `/episodes` | `Episodes` | Pronaći kliničku epizodu. | kliničke uloge | 1 | popis epizoda — `ESSENTIAL` | Pojam nije intuitivan recepciji; ne treba biti primarna navigacija. |
| `/episodes/new` | `EpisodeForm` | Otvoriti kliničku epizodu. | liječnik i ovlaštene kliničke uloge | 2 | pacijent i klinički kontekst — `ESSENTIAL`; tehnički identifikatori — `TECHNICAL-ONLY` | Zadržati kao kontekstualnu kliničku radnju. |
| `/episodes/:id` | `EpisodeDetail` | Pregledati sadržaj jedne epizode. | liječnik i ovlaštene kliničke uloge | 6 | klinički sadržaj — `ESSENTIAL`; izvor/provenance — `CONTEXTUAL`; audit — `HISTORICAL` | Ne smije konkurirati kanonskom workspaceu pregleda. |

### 5.2 Klinički sadržaj i radni alati

| Ruta | Zaslon | Primarna svrha i radnja | Uloge | API deklaracije | Vidljivi sadržaj / klasifikacija | Nalaz |
| --- | --- | --- | --- | ---: | --- | --- |
| `/clinical-documents` | `ClinicalDocuments` | Pronaći i otvoriti klinički dokument. | liječnik, pregledavatelj dokumenata, ovlaštene uloge | 2 | pacijent, vrsta, datum, status — `ESSENTIAL`; sirovi ID-evi i tehničko stanje — `TECHNICAL-ONLY` | Osam stupaca je previše za primarnu pretragu. |
| `/clinical-documents/:id` | `ClinicalDocumentDetail` | Pregledati izvor, OCR/izvod i status pregleda. | liječnik, pregledavatelj dokumenata | 4 | original i klinički relevantni metapodaci — `ESSENTIAL`; OCR/AI — `CONTEXTUAL`; provider/confidence/provenance — `ADVANCED` | Izvor mora ostati vidljiv i nadređen izvedenim slojevima. |
| `/laboratory` | `Laboratory` | Naručiti/pratiti laboratorijske nalaze i unijeti rezultat. | liječnik, sestra/tehničar, ovlaštene uloge | 3 | pacijent, pretrage, uzorak, rezultat — `ESSENTIAL`; zaključak — `CONTEXTUAL`; tehnički status — `ADVANCED` | 28 naslova i osam izvornih gumba stvaraju fragmentaciju jednog posla. |
| `/therapies` | `Therapies` | Evidentirati i pregledati terapiju. | liječnik i ovlaštene kliničke uloge | 3 | aktivna terapija — `ESSENTIAL`; povijest — `HISTORICAL`; tehnički status — `ADVANCED` | Primarni i povijesni prikaz treba jasnije razdvojiti. |
| `/gastroenterology` | `GastroenterologyWorkspace` | Provesti gastroenterološki pregled/pretragu. | liječnik, podržavajuće kliničke uloge | 5 | anamneza, status/nalaz, mišljenje, preporuke, dijagnoze — `ESSENTIAL`; izvori i struktura obrasca — `CONTEXTUAL` | Treba ostati vezan uz kanonsku aktivnost, a ne djelovati kao zaseban sustav. |
| `/workflow` | `WorkflowTasks` | Pronaći otvorene zadatke. | operativne uloge prema dopuštenju | 4 | moji/otvoreni zadaci — `ESSENTIAL`; tehnički status — `ADVANCED` | Naziv „Zadaci” je jasniji od tehničkog workflow pojma. |
| `/workflow/:id` | `WorkflowTaskDetail` | Riješiti jedan zadatak. | vlasnik/ovlaštena uloga | 3 | opis i sljedeća radnja — `ESSENTIAL`; povijest — `HISTORICAL` | Jedna primarna radnja treba biti očita. |
| `/knowledge` | `KnowledgeProtocols` | Pronaći postupnik ili smjernicu. | liječnik, administrator sadržaja | 1 | naslov i kategorija — `ESSENTIAL`; sažetak — `CONTEXTUAL` | Popis treba ostati naslovno orijentiran. |
| `/knowledge/:id` | `KnowledgeProtocolDetail` | Pročitati postupnik po naslovima i otvoriti objašnjenja. | liječnik, administrator sadržaja | 1 | naslovi pravila — `ESSENTIAL`; objašnjenja/izvori — `CONTEXTUAL`; verzija/review — `ADVANCED` | Progresivno otkrivanje već odgovara cilju. |

### 5.3 Financije, zalihe i administracija

| Ruta | Zaslon | Primarna svrha i radnja | Uloge | API deklaracije | Vidljivi sadržaj / klasifikacija | Nalaz |
| --- | --- | --- | --- | ---: | --- | --- |
| `/invoices` | `Invoices` | Pronaći račun i vidjeti stanje naplate. | naplata, administrator | 1 | pacijent, iznos, status, datum — `ESSENTIAL`; tehnički identifikator — `TECHNICAL-ONLY` | Pet stupaca i jedna radnja čine dobar lean popis. |
| `/inventory` | `Inventory` | Uočiti stanje zalihe i evidentirati promjenu. | voditelj zaliha, administrator | 3 | proizvod, raspoloživo, prag — `ESSENTIAL`; serija/lot — `CONTEXTUAL`; povijest — `HISTORICAL` | Potrebno odvojiti dnevne iznimke od kataloškog održavanja. |
| `/suppliers` | `Suppliers` | Pronaći i održavati dobavljača. | voditelj zaliha, administrator | 1 | dobavljač i kontakt — `ESSENTIAL`; povijest — `HISTORICAL` | Prikladno kao sekundarni nabavni alat. |
| `/purchase-orders` | `PurchaseOrders` | Izraditi i pratiti narudžbenicu. | voditelj zaliha, administrator | 4 | dobavljač, stavke, status — `ESSENTIAL`; tehnički događaji — `ADVANCED` | Dvije istovremene radnje su prihvatljive ako je primarna jasno označena. |
| `/services` | `Services` | Održavati katalog usluga. | administrator | 3 | naziv, trajanje, cijena, klinika/prostorija — `ESSENTIAL`; skriveno/obrisano — `CONTEXTUAL` | Administrativni zaslon, ne pripada operativnom radu liječnika. |
| `/clinics` | `Clinics` | Održavati klinike, prostorije i osoblje. | administrator | 3 | klinike/prostorije ili osoblje — `ESSENTIAL`; dostupnost — `CONTEXTUAL`; audit — `HISTORICAL` | Pet izvornih gumba i 18 naslova; podjela na dva jasna konteksta je nužna. |
| `/modules` | `Modules` | Uključiti/isključiti dostupne module. | administrator | 1 | modul i stanje — `ESSENTIAL`; tehnički opis — `ADVANCED` | Ne smije biti vidljivo operativnim ulogama. |
| `/audit-log` | `AuditLog` | Istražiti tko je napravio koju promjenu. | administrator/auditor prema RBAC-u | 1 | vrijeme, akter, radnja, entitet — `ESSENTIAL`; sirovi payload — `ADVANCED` | Pet stupaca je prihvatljivo; detalj otvarati na zahtjev. |
| `/api-keys` | `ApiKeys` | Upravljati ograničenim integracijskim ključevima. | administrator | 2 | naziv, scope, status — `ESSENTIAL`; identifikator i tehnički metapodaci — `ADVANCED` | Sigurnosno osjetljiv zaslon mora ostati izvan svakodnevne navigacije. |
| `/readiness` | `Readiness` | Procijeniti tehničku/pilot spremnost sustava. | administrator/podrška | 1 | blokatori i potrebna provjera — `ESSENTIAL`; sigurnosni kontekst — `CONTEXTUAL`; fiskalizacija/provider/tehnički gate — `TECHNICAL-ONLY`; povijest — `HISTORICAL` | 22 gumba, 9 naslova, 4 metrike, 8 stupaca i 2843 px: najgušći administratorski zaslon. |

### 5.4 Prijava i sintetički/demo alati

| Ruta | Zaslon | Primarna svrha | Uloge | API deklaracije | Klasifikacija | Nalaz |
| --- | --- | --- | --- | ---: | --- | --- |
| `/login` | `Login` | Sigurna prijava. | svi korisnici | 0 | vjerodajnice i pogreška — `ESSENTIAL` | Zadržati minimalno. |
| `/program1/synthetic-review` | `SyntheticReviewWorkspace` | Pregled sintetičkih scenarija Programa 1. | administrator/demo | 0 | demo evaluacija — `TECHNICAL-ONLY` | Ne pripada produkcijskoj operativnoj navigaciji. |
| `/program1/synthetic-evaluation` | `SyntheticEvaluationRunner` | Pokrenuti sintetičku evaluaciju. | administrator/demo | 0 | demo evaluacija — `TECHNICAL-ONLY` | Zadržati jasno označeno kao demo. |

## 6. Inventura po ulozi

| Uloga | Najčešći zadaci | Četiri najvažnija zaslona | Što nije primarno | Radnje koje trebaju biti udaljene 1–2 klika | Predloženi početni zaslon |
| --- | --- | --- | --- | --- | --- |
| Liječnik | Vidjeti današnje pacijente; otvoriti pregled; pregledati donesene dokumente; dovršiti i potpisati nalaz. | Danas; Tijek pacijenta; Pregled; Dokument pacijenta | zalihe, dobavljači, API ključevi, globalni audit, readiness | Otvori pregled; otvori izvorni dokument; potpiši nalaz; vrati na današnji red | Danas, filtrirano na prijavljenog liječnika |
| Sestra/tehničar | Vidjeti red; pripremiti pacijenta/prostoriju; evidentirati materijal/uzorak; predati liječniku. | Danas; Prijem; Tijek pacijenta; Laboratorij/Materijal | računi, API ključevi, konfiguracija modula, tehnički readiness | Otvori prijem; označi provjereno; evidentiraj materijal; otvori nalog za uzorak | Danas, filtrirano na kliniku/prostoriju |
| Tajnica/administratorica recepcije | Pronaći/dodati pacijenta; naručiti; prijaviti dolazak; ispraviti kontakt. | Danas; Pacijenti; Naručivanje; dashboard-native Prijem | klinički sažetak, terapijska odluka, audit payload, zalihe | Dodaj pacijenta iz prazne pretrage; novi termin; otvori prijem; potvrdi podatke | Danas |
| Naplata | Uočiti dovršene usluge; otvoriti račun; evidentirati plaćanje; pronaći dug. | Danas; Računi; Tijek pacijenta (naplata); Pacijent | klinički detalji, OCR, priprema, inventar, dokument review | Pripremi račun; izdaj račun; evidentiraj uplatu; vrati na popis | Danas, filtrirano na „čeka naplatu” |
| Voditelj zaliha | Uočiti manjak; pregledati potrošnju; naručiti; zaprimiti robu. | Inventar; Narudžbenice; Dobavljači; Danas (samo iznimke materijala) | anamneza, pacijentski dokumenti, naplata, prijem | Otvori artikl ispod praga; nova narudžbenica; zaprimi; pogledaj potrošnju | Inventar s iznimkama |
| Administrator | Upravljati klinikama/osobljem/uslugama; istražiti audit; provjeriti spremnost. | Klinike i osoblje; Usluge; Evidencija aktivnosti; Spremnost | sadržaj pojedinog pregleda bez operativne potrebe | Dodaj osobu/prostoriju/uslugu; promijeni radno vrijeme; otvori audit detalj | Administrativni pregled, ne klinički Danas |
| Pregledavatelj dokumenata | Pronaći neriješene dokumente; otvoriti original; pregledati klasifikaciju; potvrditi/odbiti. | Dokumenti; Detalj dokumenta; Pacijent; Tijek pacijenta | naplata, zalihe, naručivanje, administracija klinike | Otvori original; označi pregledano; vrati na sljedeći dokument; otvori pacijenta | Dokumenti, filtrirano na „za pregled” |

## 7. Sintetički prolazi najčešćih zadataka

Broj klikova je procjena do prve korisne akcije na postojećem sučelju. Ne
uključuje tipkanje i ne predstavlja završenu ljudsku usability studiju.

| Scenarij | Početak | Procjena klikova | Zasloni / navigacijski pojmovi | Je li kritično iznad pregiba? | Nepotreban sadržaj tijekom zadatka |
| --- | --- | ---: | --- | --- | --- |
| Recepcija: pronaći postojeću pacijenticu i naručiti je | Danas | 3–4 | Pacijenti → rezultat → Novi termin | Da, radnja je u zaglavlju pacijenta | dvostruki metrički blokovi pacijenta prije identiteta |
| Recepcija: pacijent je stigao i treba prijem | Danas | 1 | primarna radnja `Otvori prijem` | Da | zasebna ruta Prijem i puni workspace nisu potrebni za početak |
| Liječnik: otvoriti sljedeći pregled | Danas | 1 | primarna radnja `Otvori pregled` | Da | dokumenti/priprema koji ne traže akciju |
| Liječnik: otvoriti izvor dokumenta iz tijeka | Tijek pacijenta | 2–3 | Dokumenti i priprema → dokument → original | Djelomično; ovisi o fazi | timeline i AI sažetak učitani su i kad nisu otvoreni |
| Sestra: evidentirati potrošni materijal aktivnosti | Danas | 2–3 | pacijent → Materijal → unos | Djelomično | naplata, sažetak i povijest nisu potrebni prije unosa |
| Naplata: završeni pregled pretvoriti u račun | Danas | 1–2 | filter/status → primarna radnja naplate | Da | klinički sadržaj nije potreban ako su gateovi riješeni |
| Administrator: promijeniti radno vrijeme osobe | Danas | 3–4 | Više → Klinike i osoblje → Osoblje → sat | Ne; funkcija je skrivena pod generičkim „Više” | klinike/prostorije ako je odabran kontekst osoblja |
| Pregledavatelj: riješiti sljedeći dokument | Dokumenti | 1–2 | red dokumenta → detalj/review | Da | sirovi ID i tehnički metapodaci u glavnoj tablici |

## 8. Vizualni baseline

Za svaki zaslon postoje četiri datoteke oblika
`<zaslon>-<širina>x<visina>.jpg`.

| Zaslon | Rute | Datoteke | Glavni nalaz |
| --- | --- | --- | --- |
| AppShell + Danas | `/` | `app-shell-dashboard-{1440x900,1280x800,1024x768,768x1024}.jpg` | Primarna navigacija je mirna, ali „Više” skriva previše domena; mobilni izbornik troši velik dio početnog prikaza. |
| Tijek pacijenta | `/journeys/17` | `journey-workspace-{...}.jpg` | Jasna sljedeća radnja, ali pet faza i više pomoćnih sekcija ostaju istodobno prisutni. |
| Pacijent | `/patients/3` | `patient-detail-{...}.jpg` | Dupli zbrojevi i širok skup radnji guraju identitet i relevantnu povijest niže. |
| Dokumenti | `/clinical-documents` | `clinical-documents-{...}.jpg` | Tablica je funkcionalna, ali osam stupaca miješa operativno i tehničko. |
| Novi termin | `/appointments/new` | `appointment-form-{...}.jpg` | Redoslijed polja je jasan; treba zaštititi brzu pretragu pacijenta i vidljivost konflikata. |
| Računi | `/invoices` | `invoices-{...}.jpg` | Najčišći popis: pet stupaca i mali broj radnji. |
| Audit | `/audit-log` | `audit-log-{...}.jpg` | Operativni popis je prihvatljiv; sirovi detalj treba ostati na zahtjev. |
| Spremnost | `/readiness` | `readiness-{...}.jpg` | Tehničko i poslovno stanje stopljeni su u jedan dugačak administratorski prikaz. |

### 8.1 Mjerenje sadržajne gustoće na 1440 × 900

| Zaslon | Gumbi | Kartice | Naslovi | Tabovi | Stupci tablice | Visina dokumenta | Ocjena sadržaja |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Danas | 11 | 2 | 6 | 0 | 0 | 1967 px | Primarni red i status `ESSENTIAL`; dodatni filtri `CONTEXTUAL`; normalni detalji skriveni ispravno. |
| Tijek pacijenta | 15 | 0 | 13 | 5 | 0 | 1018 px | Sljedeća radnja `ESSENTIAL`; neaktivne faze `CONTEXTUAL`; timeline/AI `ADVANCED`; ponovljeni statusi mogu biti `REDUNDANT`. |
| Pacijent | 25 | 14 | 28 | 11 | 0 | 3263 px | Identitet/sljedeći termin `ESSENTIAL`; domenski sažeci `CONTEXTUAL`; audit `HISTORICAL`; dva metrička bloka `REDUNDANT`; tehnički ID-evi `TECHNICAL-ONLY`. |
| Dokumenti | 4 | 0 | 6 | 0 | 8 | 900 px | pacijent/vrsta/datum/status `ESSENTIAL`; izvor `CONTEXTUAL`; interni ID i tehničko stanje `TECHNICAL-ONLY`. |
| Novi termin | 8 | 0 | 6 | 0 | 0 | 900 px | polja termina `ESSENTIAL`; pomoć i preview `CONTEXTUAL`; tehnički konfliktni detalj `ADVANCED`. |
| Računi | 1 | 0 | 6 | 0 | 5 | 900 px | iznos/status/pacijent `ESSENTIAL`; povijest `HISTORICAL`; interni ID `TECHNICAL-ONLY`. |
| Audit | 1 | 0 | 7 | 0 | 5 | 900 px | vrijeme/akter/radnja `ESSENTIAL`; prije/poslije `ADVANCED`; stari zapisi `HISTORICAL`; request ID `TECHNICAL-ONLY`. |
| Spremnost | 22 | 0 | 9 | 0 | 8 | 2843 px | blokatori `ESSENTIAL`; objašnjenje `CONTEXTUAL`; provider/fiskalizacija/drift `TECHNICAL-ONLY`; završene provjere `HISTORICAL`. |

## 9. Najvažniji nalazi

1. **Pacijent nije „radni stol”, nego agregat svega.** `PatientDetail` učitava
   jedanaest domena i prikazuje dva sloja zbrojeva prije identiteta. Najprije
   treba pokazati identitet, današnji/sljedeći kontekst i jednu primarnu radnju,
   a ostalo učitavati po kartici.
2. **Tijek pacijenta dobro objašnjava sljedeću radnju, ali previše konteksta
   učitava unaprijed.** Timeline, AI sažetak i dokumenti trebaju biti lijeno
   učitani kad ih korisnik otvori ili kad trenutna faza to zahtijeva.
3. **Jedan generički „Više” povećava trošak pronalaska.** Sekundarne domene
   trebaju biti grupirane prema poslu i ulozi, uz jasan naziv aktivne uloge.
4. **Normalna stanja zauzimaju prostor kao i iznimke.** Dokumenti, priprema i
   checkliste trebaju biti vidljivi prvenstveno kada traže akciju.
5. **Tehnički i operativni sadržaj često su u istoj ravnini.** Sirovi ID-evi,
   provider statusi, drift i payload pripadaju naprednim administratorskim
   detaljima.
6. **Postoje dobri lean obrasci koje treba ponoviti.** Danas koristi jednu
   primarnu radnju, a Računi imaju mali broj stupaca i kontrola.
7. **Jezik nije dosljedan.** Primjeri su `Patient Workspace`, `confirmed`,
   `primary`, `noop` i nazivi bez hrvatskih dijakritika. Prijevod mora biti
   semantički, ne samo zamjena stringa.

## 10. Ciljni prije/poslije model za sljedeće faze

| Područje | Prije | Cilj poslije |
| --- | --- | --- |
| Shell | četiri primarne stavke + šest domena pod „Više”; slab opis uloge | navigacija po odgovornosti; jasna aktivna uloga i klinika; napredna administracija odvojena |
| Danas | dobar operativni red, ali duga vremenska os i dio sekundarnih kontrola | zadržati jednu radnju; iznimke prije normalnog statusa; filtri progresivno |
| Pacijent | 11 mount izvora, 14 kartica, 25 gumba, dvostruki zbrojevi | identitet + aktualni kontekst; 4–5 domenskih tabova; lazy loading; jedna glavna radnja |
| Tijek pacijenta | cijeli proces i pomoćni slojevi na jednom zaslonu | trenutačna faza u fokusu; završene/buduće faze sažete; izvori na zahtjev |
| Dokumenti | operativni i tehnički stupci zajedno | pacijent/vrsta/datum/status u popisu; provenance i OCR u detalju |
| Spremnost | poslovni i tehnički gateovi u 2843 px | blokatori i odluka prvo; tehnička dijagnostika odvojeno i sklopljeno |

## 11. Prioritet sljedećih faza

1. **Faza B — semantički shell i navigacija po ulozi.** Ne mijenjati
   autorizaciju; mijenja se samo vidljiv redoslijed i naziv grupa.
2. **Faza C — lean `PatientDetail`.** Ukloniti dvostruke metrike, ograničiti
   primarne radnje i uvesti lazy domenske tabove.
3. **Faza D — fokusirani `PatientJourneyWorkspace`.** Jedna trenutačna faza,
   progresivno otkrivanje timelinea/dokumenata/AI sloja.
4. **Faza E — dokumenti, računi i audit tablice.** Zadržati operativne stupce,
   premjestiti tehničke detalje u kontrolirani detalj.
5. **Faza F — razdvojiti poslovnu spremnost od tehničke dijagnostike.**
6. **Faze G–J — dosljedan jezik, responsive provjera, uloge, regresije i
   završna ljudska sintetička evaluacija.**

## 12. Sigurnosne i kliničke regresije koje se ne smiju dogoditi

Svaka sljedeća faza mora dokazati:

- UI skrivanje ne zamjenjuje RBAC i ne širi pristup podacima;
- globalni identitet pacijenta ne prenosi kliničke dokumente između ustanova;
- izvorni klinički dokument ostaje izvor istine;
- potpisani nalaz ostaje nepromjenjiv i verzijski precizan;
- CSRF, session i same-origin model ostaju nepromijenjeni;
- audit ostaje potpun i ne izlaže PHI ili tajne;
- kliničke odluke ostaju ljudske;
- „normalno” skriveni detalj postaje vidljiv kad postoji problem ili zahtjev za
  pregled;
- promjena klinike ne smije izgubiti nespremljenu kliničku skicu;
- smanjenje broja klikova ne smije zaobići obveznu potvrdu, potpis ili gate.

## 13. Odluka Faze A

Inventura potvrđuje da je pojednostavljenje opravdano i da se može provoditi
inkrementalno bez promjene domenskog modela. Najveća vrijednost je u
reorganizaciji `PatientDetail`, zatim u fokusiranju `PatientJourneyWorkspace` i
jasnijem grupiranju sekundarne navigacije.

Faza A ne autorizira uklanjanje podataka ili poslovnih provjera. Svaka promjena
u sljedećoj fazi mora imati usporedbu prije/poslije, ciljane testove i
provjeru po ulozi.
