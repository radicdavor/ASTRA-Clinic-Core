# Program 2 Phase H — Potpisani nalazi, ispis i dostava

## Ishod

Ljudski potpis dovršenog kliničkog obrasca sada stvara jedan izvorno povezan `ClinicalDocument` i jednu nepromjenjivu verziju `SignedClinicalReport`. Dokument pripada pacijentu, dolasku i pojedinoj aktivnosti.

## Nepromjenjivost i ispravci

Potpisana verzija čuva:

- strukturirane vrijednosti obrasca
- renderirani sadržaj
- definiciju i verziju obrasca
- autora/potpisnika i vrijeme potpisa
- vrstu nalaza
- aktivnost, dolazak i pacijenta
- vezu na klinički dokument

Kontrolirani ispravak otvara novi obrazac. Novi potpis stvara novu verziju izvještaja, označava koju verziju zamjenjuje i ne prepisuje izvorni potpisani sadržaj.

## Dokumenti ovog dolaska

Radni prostor prikazuje centar `Dokumenti ovog dolaska` s naslovom, aktivnošću, verzijom, potpisnikom, datumom, brojem ispisa i stanjem dostave. Dostupni su pregled točne verzije, ispis i odabir više potpisanih dokumenata za dostavu.

Ispis najprije bilježi auditirani `ReportPrintEvent`, a pregled za ispis renderira točno spremljeni potpisani sadržaj.

## Dostava

Endpoint za dostavu prihvaća samo postojeće potpisane verzije istog dolaska. Zamijenjena verzija zahtijeva dodatnu izričitu potvrdu.

U trenutačnom autoriziranom okruženju dostava koristi `local_demo` stub i stanje `queued_stub`. To znači da je zahtjev evidentiran, ali se ne tvrdi da je e-mail poslan ili dostavljen pacijentu. Produkcijski pružatelj e-pošte nije spojen.

## API

- `GET /api/patient-journeys/{journey_id}/visit-documents`
- `GET /api/signed-reports/{report_id}`
- `POST /api/signed-reports/{report_id}/print`
- `POST /api/patient-journeys/{journey_id}/visit-documents/deliver`
- `GET /api/signed-reports/{report_id}/delivery-history`

## Provjera

Migracija `0050_signed_reports` prolazi od prazne PostgreSQL baze do `head`, downgrade jedne revizije i ponovni upgrade. Testovi potvrđuju stvaranje kliničkog dokumenta, očuvanje starije verzije, ispis, demo/stub dostavu i blokadu nenamjernog slanja zamijenjene verzije. Frontend typecheck, interaktivni testovi i produkcijski build prolaze.
