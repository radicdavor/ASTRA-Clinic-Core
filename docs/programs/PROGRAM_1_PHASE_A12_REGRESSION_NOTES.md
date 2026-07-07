# Program 1 - Phase A12 Regression Notes

## 1. Svrha

Ove biljeske zatvaraju Program 1 Phase A12 - Split System Public Config Route.

A12 je infrastrukturni route split. Nije nova klinicka funkcionalnost, nije produkcijsko odobrenje, nije real-data odobrenje, nije compliance odobrenje i nije tvrdnja da je ASTRA certificirani EMR ili medicinski uredaj.

## 2. Implementirano

- Dodan je `backend/app/api/routes/system.py`.
- `GET /api/public-config` je premjesten iz `core.py` u sistemski route modul.
- `backend/app/main.py` registrira `system.router`.
- Frontend smoke provjera cuva da `system.py` sadrzi `/public-config` i da je `system.router` registriran.

Endpoint URL ostaje isti:

- `GET /api/public-config`

## 3. Namjerno nije implementirano

- novi system/config model
- promjena public config response ugovora
- real-data odobrenje
- produkcijske ili certifikacijske tvrdnje
- Task engine
- Clinical Readiness Gate
- Workflow Engine
- Episode-Based Care kao primary workflow

## 4. Preporuceni sljedeci zadatak

`Program 1 Phase A13 - Split ClinicalDocument Routes`

Razlog: ClinicalDocument helperi su vec u servisu, a A8/A11 smoke coverage cuva Patient Knowledge invariants.
