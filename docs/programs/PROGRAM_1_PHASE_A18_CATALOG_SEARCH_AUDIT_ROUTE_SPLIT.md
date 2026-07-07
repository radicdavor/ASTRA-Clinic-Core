# Program 1 Phase A18 - Catalog, Search i Audit Route Split

## 1. Svrha

A18 izdvaja preostale catalog, search i audit rute iz `backend/app/api/routes/core.py`.

Ovo je zavrsno ciscenje trenutnog route modularization passa. Nije nova klinicka funkcionalnost, ne mijenja workflow i ne mijenja javne API adrese.

## 2. Trenutni problem

Nakon A17 `core.py` je mali, ali jos uvijek mijesa nepovezane operativne rute:

- catalog/configuration rute za usluge, module, providere, sobe i klinike
- globalnu operativnu pretragu
- raw audit log prikaz

Te cjeline imaju razlicite odgovornosti i trebaju zivjeti u zasebnim route modulima kako `core.py` vise ne bi bio opci spremnik za nepovezane domene.

## 3. Ciljni route moduli

Ciljni backend moduli su:

- `backend/app/api/routes/catalog.py`
- `backend/app/api/routes/audit.py`
- `backend/app/api/routes/search.py`

`catalog.py` sadrzi operativni katalog i konfiguracijske rute:

- `GET /api/services`
- `POST /api/services`
- `GET /api/clinics`
- `GET /api/modules`
- `GET /api/providers`
- `GET /api/rooms`

`audit.py` sadrzi raw audit log rute:

- `GET /api/audit-log`

`search.py` sadrzi operativnu cross-object pretragu:

- `GET /api/search`

## 4. Zasticeni invariants

A18 mora sacuvati:

- postojece API adrese
- postojece permissione
- postojece response schema
- postojece audit ponasanje
- Operational Readiness kao operational readiness, ne Clinical Readiness Gate
- search kao operativni lookup, ne klinicko zakljucivanje
- catalog kao operativnu konfiguraciju, ne clinical workflow
- audit kao rekonstrukcijsku/evidence infrastrukturu, ne Outcome Evidence objekt

## 5. Izvan scopea

A18 ne uvodi:

- Clinical Readiness Gate
- Task engine
- Workflow Engine
- Episode-Based Care reaktivaciju
- Outcome Evidence
- novi search engine
- real AI provider
- real OCR provider
- stvarne podatke pacijenata
- produkcijske ili certifikacijske tvrdnje
- migracije baze

## 6. Ocekivani ishod

Nakon A18 `core.py` treba biti uklonjen ili sveden na minimalni dokumentirani compatibility router. Ako nema preostalih ruta, `core.router` se uklanja iz `backend/app/main.py`.

Korisnik ne bi smio primijetiti funkcionalnu promjenu. Dobitak je jasnija arhitektura i zavrsen route modularization pass prije Phase A closure odluke.
