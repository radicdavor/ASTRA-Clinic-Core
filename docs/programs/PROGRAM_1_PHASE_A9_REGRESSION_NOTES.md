# Program 1 - Phase A9 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A9 - Core Route Modularization Pass.

A9 je tehnicki hardening i modularizacijski pass. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- ClinicalDocument route helper logika premjestena je iz `core.py` u `backend/app/services/clinical_documents.py`.
- Operational Readiness builder premjesten je iz `core.py` u `backend/app/services/readiness.py`.
- `/api/readiness` sada ostaje tanki endpoint koji poziva servisni builder.
- ClinicalDocument endpointi i dalje koriste iste URL-ove i isti API ugovor.
- `core.py` je smanjen za otprilike 250 linija bez migracija i bez novih objekata.

## 3. Namjerno nije implementirano

- Task engine
- Clinical Readiness Gate
- Episode-Based Care kao primary workflow
- Workflow Engine
- Outcome Evidence object
- real AI provider
- real OCR provider
- novi ClinicalDocument schema/model fieldovi
- nove tablice ili migracije
- stvarni pacijentovi podaci
- produkcijske ili certifikacijske tvrdnje

## 4. Regression checks

Pokrenuto tijekom A9:

- `python -m py_compile app\api\routes\core.py app\services\clinical_documents.py app\services\readiness.py` - proslo
- `git diff --check` - proslo
- `npm run typecheck` - proslo
- `npm run build` - proslo uz postojece Tailwind/React Router warninge
- `npm run smoke` - proslo nakon uskladivanja smoke provjere s novim `readiness.py` servisom

Backend `pytest` nije lokalno pokrenut jer je jedini dostupan Python runtime `3.14`, a zakljucani dependency `psycopg-binary==3.2.3` nema dostupnu distribuciju za taj runtime. Potrebno je pokrenuti backend testove kroz podrzani Python runtime ili Docker.

## 5. Preostali rizici

- `core.py` je manji, ali i dalje sadrzi vise domena u jednom route modulu.
- FastAPI route moduli jos nisu razdvojeni po domenama.
- A9 ne zamjenjuje A8 regression gate; buduci rad ga mora nastaviti pokretati.
- Lokalna backend test infrastruktura treba podrzani Python runtime za puni `pytest`.

## 6. Go/No-Go

Go za usku A9 modularizaciju.

No-Go za sirenje prema Task engineu, Clinical Readiness Gateu, Workflow Engineu, Outcome Evidenceu ili Episode-Based Careu prije posebne arhitektonske odluke.

## 7. Preporuceni sljedeci zadatak

`Program 1 Phase A10 - Core Route Domain Split Plan`

Razlog: `core.py` je vec smanjen, ali i dalje sadrzi route odgovornosti za vise domena. Prije daljnjeg cijepanja treba planirati granice po domenama i test coverage koji cuva URL/API kompatibilnost.
