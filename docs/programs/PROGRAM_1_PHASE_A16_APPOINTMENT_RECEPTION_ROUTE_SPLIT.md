# Program 1 Phase A16 - Appointment i Reception Route Split

## Svrha

Ovaj dokument definira A16 korak modularizacije backend ruta za termine, dnevni raspored i recepcijski prijem.

A16 nije nova funkcionalnost. Cilj je smanjiti odgovornost `core.py` i premjestiti postojece operativne API-je u jasnije route module:

- `appointments.py` za termine i dnevni raspored
- `reception.py` za recepcijski prikaz dana i oznacavanje dolaska pacijenta

Ovaj korak nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## Zasticeni API ugovor

Sljedeci postojece API adrese moraju ostati iste:

- `POST /api/appointments`
- `GET /api/appointments`
- `GET /api/appointments/{appointment_id}`
- `PATCH /api/appointments/{appointment_id}`
- `DELETE /api/appointments/{appointment_id}`
- `GET /api/schedule/day`
- `GET /api/reception/day`
- `POST /api/appointments/{appointment_id}/mark-arrived`

Frontend ne smije morati mijenjati adrese. Audit dogadaji, dozvole i response modeli moraju ostati kompatibilni s prethodnim stanjem.

## Granice odgovornosti

`appointments.py` odgovara za:

- kreiranje termina
- pretragu i filtriranje termina
- detalj termina
- izmjenu i brisanje termina
- dnevni raspored
- validaciju opcionalne veze termina s eksperimentalnom epizodom

`reception.py` odgovara za:

- recepcijski dnevni prikaz po slotovima
- filtre recepcije po klinici, sobi, lijecniku, usluzi i statusu
- oznacavanje pacijenta kao pristiglog
- opcionalnu dopunu podataka pacijenta pri prijemu
- audit provjere identiteta i dolaska

`core.py` nakon A16 smije zadrzati preostale domenske rute koje jos nisu izdvojene, ali ne smije vise nositi glavnu odgovornost za termine i recepciju.

## No-Go podrucja

A16 ne uvodi:

- Clinical Readiness Gate
- Task engine
- Workflow Engine
- Episode-Based Care kao primarni tijek
- Outcome Evidence objekt
- stvarni AI provider
- stvarni OCR provider
- stvarne podatke pacijenata
- produkcijske ili certifikacijske tvrdnje

Episode Engine ostaje eksperimentalan/deferred. Termini i dalje smiju postojati bez epizode.

## Regresijske provjere

Minimalne provjere za A16:

- backend import/compile provjera za nove route module
- backend testovi u podrzanom runtimeu
- frontend typecheck
- frontend build
- frontend smoke provjera
- `git diff --check`

Ako Docker ili drugi podrzani backend runtime nije dostupan, to se mora evidentirati kao validacijski rizik.

## Ocekivani ishod

Nakon A16 korisnik ne bi smio primijetiti funkcionalnu promjenu. Korist je arhitektonska: termin, dnevni raspored i recepcija postaju zasebne, citljive cjeline koje se mogu dalje stabilizirati bez povecavanja `core.py`.

## Implementacijsko ozicenje

A16 zadrzava postojece API ugovore, ali mijenja mjesto implementacije:

| Podrucje | Route modul | Napomena |
| --- | --- | --- |
| Termini | `backend/app/api/routes/appointments.py` | Kreiranje, popis, detalj, izmjena, brisanje i dnevni raspored. |
| Recepcija | `backend/app/api/routes/reception.py` | Recepcijski dnevni slotovi i oznacavanje dolaska pacijenta. |
| Materijali i racuni povezani s terminom | `backend/app/api/routes/inventory.py` | Ostaju u inventory/billing kontekstu jer mijenjaju zalihe i racune. |
| Epizodni prikaz termina | `backend/app/api/routes/core.py` | Privremeno ostaje uz eksperimentalni/deferred Episode Engine dok se taj blok ne izdvoji zasebno. |

`backend/app/main.py` registrira `appointments.router` i `reception.router` prije preostalog `core.router`, tako da javne adrese ostaju kompatibilne s postojecom frontend aplikacijom i testovima.

Smoke provjera dodatno cuva prisutnost:

- `appointments.router`
- `reception.router`
- `/api/appointments`
- `/api/schedule/day`
- `/api/reception/day`
- `/api/appointments/{appointment_id}/mark-arrived`
