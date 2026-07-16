# Program 2 Phase G — Intervencije, uzorci i patologija

## Ishod

Jedna aktivnost dolaska sada može evidentirati više izvedenih intervencija te, kada je klinički primjenjivo, otvoriti jedan sljediv patološki slučaj s jednim ili više uzoraka.

## Model

- `ProcedureIntervention` pripada točno jednoj `JourneyActivity`.
- `PathologyCase` pripada točno jednoj aktivnosti i jednom pacijentu.
- `PathologySpecimen` pripada patološkom slučaju i zadržava vezu na intervenciju iz koje je nastao.
- `PathologyReportLink` povezuje izvorni klinički dokument s patološkim slučajem.

Podržane intervencije su biopsija, polipektomija, injekcija, postavljanje klipse, dilatacija, hemostaza, uklanjanje stranog tijela i druga ručno opisana intervencija.

## Sigurnosna pravila

- Uzorak se može evidentirati samo za biopsiju ili dohvaćenu polipektomiju.
- Nalaz mora pripadati istom pacijentu kao aktivnost i patološki slučaj.
- Povezivanje pristiglog nalaza postavlja stanje `clinician_review_required`.
- Samo izričita radnja ovlaštenog korisnika postavlja stanje `clinician_reviewed`.
- Sustav ne tumači nalaz kao dijagnozu, ne obavještava pacijenta automatski i ne zatvara klinički slučaj bez ljudske provjere.

## API

- `GET/POST /api/patient-journeys/{journey_id}/activities/{activity_id}/interventions`
- `POST /api/patient-journeys/{journey_id}/activities/{activity_id}/pathology-case`
- `GET /api/pathology-cases/{case_id}`
- `POST /api/pathology-cases/{case_id}/result-link`
- `POST /api/pathology-cases/{case_id}/review`

Otvaranje patološkog slučaja podržava idempotency key kako ponovljeni mrežni zahtjev ne bi stvorio duplikat.

## Migracija i provjera

Migracija `0049_interventions_pathology` je aditivna. Provjeren je cijeli `upgrade head` na praznoj PostgreSQL bazi, downgrade jedne revizije i ponovni upgrade. Ciljani testovi pokrivaju valjane i zabranjene uzorke, istovjetnost pacijenta, idempotentno otvaranje slučaja te obveznu liječničku provjeru nalaza.

## Granice faze

Ova faza daje lokalni klinički zapis i sigurnu vezu na izvorni nalaz. Slanje uzorka vanjskom laboratoriju, integracija s vanjskim patologijskim sustavom i automatska dostava pacijentu nisu aktivirani niti predstavljeni kao produkcijske integracije.
