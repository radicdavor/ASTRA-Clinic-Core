# Program 1 Phase A18 - Regression Notes

## Implemented

A18 je dovrsio trenutni backend route modularization pass.

Implementirano:

- catalog rute izdvojene su u `backend/app/api/routes/catalog.py`
- audit rute izdvojene su u `backend/app/api/routes/audit.py`
- search rute izdvojene su u `backend/app/api/routes/search.py`
- `core.py` je povucen kao route modul
- `core.router` vise nije registriran u `backend/app/main.py`
- javne API adrese su sacuvane
- smoke provjera cuva nove module i izostanak `core.router` registracije

Nije planirana korisnicka promjena ponasanja. Ovo je route organizacija.

## API paths preserved

Bez promjene ostaju:

- `GET /api/search`
- `GET /api/services`
- `POST /api/services`
- `GET /api/clinics`
- `GET /api/modules`
- `GET /api/providers`
- `GET /api/rooms`
- `GET /api/audit-log`

## Core router status

`core.py` je uklonjen kao aktivni backend route modul.

`backend/app/main.py` vise ne importira i ne registrira `core.router`.

## Not implemented

A18 nije uveo:

- Clinical Readiness Gate
- Task engine
- Workflow Engine
- Episode-Based Care kao primarni workflow
- Outcome Evidence
- novi search engine
- real AI provider
- real OCR provider
- stvarne podatke pacijenata
- produkcijske ili certifikacijske tvrdnje
- migracije baze

Search ostaje operativni lookup, catalog ostaje operativna konfiguracija, a audit ostaje raw rekonstrukcijska evidencija.

## Tests/checks

Izvedeni A18 regression gate:

- `git diff --check` - proslo
- `python -m py_compile app/main.py app/api/routes/catalog.py app/api/routes/audit.py app/api/routes/search.py` - proslo
- `docker compose run --rm -e PYTHONPATH=/app backend pytest` - proslo, 87 passed, 9 skipped
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router bundler warninge
- `npm run smoke` - proslo

`make test` nije pokrenut jer `make` nije dostupan u ovom Windows okruzenju. Ekvivalentne provjere izvedene su rucno.

## Remaining risks

- Dublja service-layer ekstrakcija za pojedine domene jos moze biti korisna.
- Frontend build warningi iz Tailwind/React Router bundla mogu ostati ako nisu posebno rijeseni.
- Catalog/search/audit split ne rjesava buduci clinical workflow dizajn.
- Nakon A18 route modularization pass treba formalno zatvoriti kroz Phase A closure odluku.

## Go / No-Go

Go za A18 ako backend testovi, frontend typecheck/build/smoke i `git diff --check` prodju.

No-Go ako:

- bilo koja catalog/search/audit API adresa nestane
- audit history ili audit storage bude promijenjen
- search pocne mijenjati podatke ili glumiti clinical reasoning
- catalog rute dobiju clinical workflow semantiku
- readiness pocne glumiti Clinical Readiness Gate

## Recommended next task

`Program 1 Phase A19 - Phase A Closure and Next-Phase Decision`

Razlog: route modularization pass je nakon A18 zavrsen. Phase A je narasla i treba formalnu closure odluku prije novih klinickih capability taskova.
