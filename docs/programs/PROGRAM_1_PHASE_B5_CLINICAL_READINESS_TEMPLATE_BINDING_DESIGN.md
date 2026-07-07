# Program 1 Phase B5 - Clinical Readiness Template Binding Design

Status: design-first, demo/pilot only

## 1. Svrha

B5 definira kako bi se Clinical Readiness templatei u buducnosti trebali sigurno vezati na stavke kataloga usluga.

Ovaj dokument je:

- design first
- bez DB modela
- bez admin editora
- bez enforcementa
- bez produkcijskih pravila
- bez certified clinical guideline claim
- bez real-data odobrenja

Svrha je zamijeniti buducu ovisnost o implicitnom keyword matchingu jasnijim, auditabilnim i upravljanim binding modelom.

B5 ne uvodi produkcijska pravila i ne mijenja odgovornost:

ASTRA prikazuje i upozorava.

Lijecnik odlucuje.

## 2. Current B4 state

B4 stanje:

- staticni templatei postoje u backend service sloju
- keyword matching prema nazivu usluge postoji
- generic fallback postoji
- preview ostaje read-only i non-blocking
- keyword matching je demo/pilot only
- nema DB template tablica
- nema template editora
- nema overridea
- nema enforcementa

B4 keyword matching je koristan za pilot, ali nije dovoljno pouzdan za produkcijska pravila.

Rizici:

- promjena naziva usluge moze promijeniti template selection
- keyword matching moze izgledati kao klinicko pravilo
- nije jasno tko je odobrio vezu usluge i templatea
- ne postoji audit trag za buduce promjene bindinga

## 3. Target future binding model

Buduci model:

Service catalog entry moze imati opcionalni `clinical_readiness_template_key`.

Konceptualno mapiranje:

| Service | Template |
| --- | --- |
| `Gastroskopija` | `gastroscopy` |
| `Kolonoskopija` | `colonoscopy` |
| `Eradikacija H. pylori` | `hpylori` |
| `Dermalni filler` | `aesthetic_injectable` |
| `PN / skinbooster` | `aesthetic_skinbooster_pn` |
| `Energy device / RF / Exion` | `aesthetic_energy_device` |

Ovo je konceptualno.

B5 ne implementira DB field.

B5 ne implementira migraciju.

B5 ne implementira UI za binding.

Buduci explicit binding mora biti pregledan kao konfiguracijska odluka, ne kao automatski zakljucak iz naziva usluge.

## 4. Binding precedence

Buduci redoslijed odabira templatea:

1. explicit service binding
2. service module/category binding
3. service-name keyword fallback
4. generic template

Trenutni runtime koristi samo:

1. service-name keyword fallback
2. generic template

Buduca implementacija treba preferirati explicit binding kada postoji.

Keyword fallback smije ostati kao demo/pilot pomoc ili kao diagnosticki fallback, ali ne kao produkcijsko pravilo.

## 5. Binding status

Konceptualni binding statusi:

| Status | Znacenje | Pouzdanost | Produkcijska uporaba | Warning/limitation |
| --- | --- | --- | --- | --- |
| `explicit` | Service ima eksplicitno odobren template binding. | Najvisa, ako postoji governance i audit. | Moguca tek nakon posebne implementacije i odobrenja. | Prikazati template key, verziju i odobrenje. |
| `module_default` | Template dolazi iz defaulta modula ili kategorije. | Srednja; zahtijeva provjeru jer modul nije uvijek postupak. | Moguca tek nakon governance modela. | Prikazati da je binding naslijeden iz modula/kategorije. |
| `keyword_fallback` | Template je odabran demo/pilot matchingom naziva usluge. | Niska do srednja u pilotu. | Ne kao produkcijsko pravilo. | `Template je odabran demo/pilot keyword matchingom prema nazivu usluge.` |
| `generic_fallback` | Nema specificnog matcha; koristi se generic template. | Niska, samo orijentacijska. | Ne kao produkcijsko pravilo. | `Nema specificnog template matcha; koristi se genericki demo/pilot template.` |
| `unbound` | Nema templatea ili je binding namjerno izostavljen. | Nema template pouzdanosti. | Nije spremno za enforcement. | Prikazati da usluga nije vezana na template. |

B5 runtime smije prikazati samo:

- `keyword_fallback`
- `generic_fallback`

Ostali statusi su dokumentirani za buducnost.

## 6. No-Go

B5 No-Go:

- nema produkcijskih pravila iz keyword matchinga
- nema skrivenih template promjena
- nema bindinga bez audita kada persistence postoji
- nema enforcementa iz unreviewed templatea
- nema AI-generated template bindinga
- nema patient-specific template mutation
- nema automatskog template bindinga iz service namea u produkciji
- nema DB fielda u ovom tasku
- nema migracije u ovom tasku
- nema template editora u ovom tasku

Ako buduci explicit binding postane potreban, mora biti zaseban, usko scopan task s auditom, rollback planom i regression gateom.
