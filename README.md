# ASTRA Clinic Core

ASTRA Clinic Core je open-source modularna jezgra za rad klinike: naručivanje pacijenata, dnevni raspored, tijek pacijenta, API integracije, audit log, osnovni RBAC, inventar, nabava i priprema naplate.

Ovo nije puni EMR ni veliki ERP. MVP je namjerno fokusiran na operativni tijek klinike i modularnu arhitekturu za buduće medicinske module.

## Tehnologije

- Backend: Python FastAPI
- Baza: PostgreSQL
- ORM: SQLAlchemy 2.x
- Migracije: Alembic
- Frontend: React, TypeScript, Vite
- Auth: JWT prijava
- Deployment: Docker Compose

## Lokalno pokretanje

1. Kopirajte primjer okoline:

```bash
cp .env.example .env
```

2. Pokrenite sustav:

```bash
docker compose up --build
```

Backend Docker entrypoint automatski pokreće:

```bash
alembic upgrade head
python -m app.seed
```

Ako ste ranije pokretali prvu MVP verziju koja je bazu stvarala preko `create_all()`, resetirajte lokalni razvojni volume prije novog starta:

```bash
docker compose down -v
docker compose up --build
```

3. Otvorite:

- Aplikacija: http://localhost:5173
- API dokumentacija: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Početna prijava:

- E-pošta: `admin@astra.local`
- Lozinka: `astra123`

## Što je uključeno

- Pacijenti: unos, popis, detalj i ažuriranje preko API-ja
- Termini: unos, popis, dnevni raspored, brza promjena statusa
- Alembic migracije umjesto startup `create_all()`
- Permission-based RBAC s eksplicitnim dozvolama po ulozi
- Strukturirani audit log s before/after JSON snapshotima i request ID-jem
- Validacija konflikta termina za liječnika i sobu
- Scoped API key autentikacija za AI agente preko `X-ASTRA-API-Key`
- Pretraživanje po pacijentu, usluzi i statusu
- Katalog usluga i modularni registar
- JWT prijava i osnovna kontrola uloga
- Audit log za create, update i delete radnje
- API rute za AI agente
- Inventar: artikli, serije, rokovi, niska zaliha, kretanja
- Nabava: dobavljači, narudžbenice, prijedlozi ponovne narudžbe
- Naplata: računi i označavanje plaćenog računa
- Predlošci potrošnje materijala po usluzi
- Automatska FEFO potrošnja materijala pri završetku termina

## Primjeri API poziva

Prijava:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@astra.local","password":"astra123"}' | jq -r .access_token)
```

Dohvat pacijenata:

```bash
curl http://localhost:8000/api/patients \
  -H "Authorization: Bearer $TOKEN"
```

Kreiranje pacijenta:

```bash
curl -X POST http://localhost:8000/api/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Petra","last_name":"Novak","phone":"+385 91 111 2222","email":"petra.novak@example.com"}'
```

Dnevni raspored:

```bash
curl "http://localhost:8000/api/schedule/day?date=2026-07-05" \
  -H "Authorization: Bearer $TOKEN"
```

AI kreiranje termina:

```bash
curl -X POST http://localhost:8000/api/ai/appointments/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":1,"service_id":1,"provider_id":1,"room_id":1,"date":"2026-07-05","start_time":"10:00","end_time":"10:45","duration_minutes":45,"status":"scheduled"}'
```

Prijedlog potrošnje materijala za termin:

```bash
curl http://localhost:8000/api/appointments/1/suggest-material-consumption \
  -H "Authorization: Bearer $TOKEN"
```

Završetak termina s automatskom FEFO potrošnjom:

```bash
curl -X POST http://localhost:8000/api/appointments/1/complete-with-consumption \
  -H "Authorization: Bearer $TOKEN"
```

Niska zaliha:

```bash
curl http://localhost:8000/api/inventory/low-stock \
  -H "Authorization: Bearer $TOKEN"
```

Kreiranje ograničenog API ključa za AI agenta:

```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Booking agent","scopes":["ai.free_slots.read","ai.patients.create","ai.appointments.create"]}'
```

## Struktura

```text
backend/app/
  main.py
  core/
  models/
  schemas/
  api/routes/
  services/
  modules/
  audit/
  auth/

frontend/src/
  api/
  components/
  pages/
  hooks/
  types/
  routes/
```

## Napomena za daljnji razvoj

Sljedeći prirodni koraci su detaljniji RBAC po dozvolama, kompletne stavke narudžbenica i računa u sučelju, fiskalizacija za Hrvatsku, integracije s računovodstvom, Google Calendar sinkronizacija i produkcijski IaC za Google Cloud.
