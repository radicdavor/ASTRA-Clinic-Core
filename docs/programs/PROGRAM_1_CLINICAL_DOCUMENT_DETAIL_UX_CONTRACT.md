# Program 1 - ClinicalDocument Detail UX Contract

## 1. Svrha

Ovaj dokument definira kako ekran detalja klinickog dokumenta mora prikazati zivotni ciklus izvora, AI prijedloga i lijecnickog pregleda.

ClinicalDocument Detail mora korisniku jasno pokazati:

- sto je izvorni dokument
- sto je AI prijedlog ekstrakcije
- sto je status lijecnickog pregleda
- kada dokument moze doprinijeti sluzbenom source-linked znanju pacijenta
- kada dokument ne doprinosi sluzbenom znanju

Ovaj dokument nije implementacija nove klinicke funkcionalnosti. Nije compliance odobrenje, nije produkcijsko odobrenje, nije odobrenje za stvarne podatke i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Zivotni ciklus prikazan na ekranu

Ekran detalja mora razlikovati ove faze:

1. Izvor je zaprimljen ili rucno kreiran.
2. AI ekstrakcija nije pokrenuta, generirana je, rucno uredjena, prihvacena kroz lijecnicki pregled, odbijena ili zamijenjena.
3. Lijecnicki pregled je u draftu, ceka pregled, pregledan je, odbijen je ili zamijenjen.
4. Dokument doprinosi Patient Clinical Knowledge samo ako je lijecnicki pregledan i source-linked.
5. Odbijanje AI prijedloga ne znaci odbijanje izvornog dokumenta.

## 3. Obavezna vizualna separacija

ClinicalDocument Detail mora vizualno odvojiti:

- identitet izvora i metapodatke
- izvorni tekst
- AI prijedlog ekstrakcije
- status AI ekstrakcije
- status lijecnickog pregleda
- akcije pregleda
- audit/timeline
- upozorenje o doprinosu sluzbenom znanju pacijenta

Korisnik ne smije steci dojam da je AI prijedlog sluzbena klinicka cinjenica prije lijecnickog pregleda.

## 4. Kanonske oznake

Status lijecnickog pregleda:

- `draft` - Izvor zaprimljen
- `needs_physician_review` - Ceka lijecnicki pregled
- `reviewed` - Lijecnicki pregledano
- `rejected` - Dokument odbijen
- `superseded` - Zamijenjeno

Status AI ekstrakcije:

- `not_run` - AI ekstrakcija nije pokrenuta
- `generated` - AI prijedlog generiran
- `edited` - AI prijedlog rucno uredjen
- `accepted` - AI prijedlog prihvacen kroz lijecnicki pregled
- `rejected` - AI prijedlog odbijen
- `superseded` - AI prijedlog zamijenjen

## 5. UX pravila

- AI prijedlog nikada nije sluzben prije lijecnickog pregleda.
- Izvorni dokument mora ostati vidljiv i nakon odbijanja AI prijedloga.
- Akcija lijecnickog pregleda mora jasno reci da dokument tada moze postati izvor za Patient Clinical Knowledge.
- Akcija odbijanja AI prijedloga mora jasno reci da odbija prijedlog, a ne izvorni dokument.
- Pregledani dokument mora jasno prikazati da moze doprinositi source-linked znanju pacijenta.
- Nepregledani dokument mora jasno prikazati da jos ne doprinosi sluzbenom znanju.
- Odbijeni i zamijenjeni dokumenti ne smiju doprinositi sluzbenom znanju.

## 6. Izvan opsega

Ovaj UX ugovor ne uvodi:

- Episode-Based Care
- Clinical Readiness Gate
- Task engine
- Outcome Evidence objekt
- formalni Medical Note output
- formalni Patient Explanation output
- Consent lifecycle
- Procedure/Treatment templates
- pravi OCR provider
- pravi AI provider
- produkcijske tvrdnje
- stvarne podatke pacijenata
