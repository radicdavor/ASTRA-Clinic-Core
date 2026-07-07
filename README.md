# ASTRA Clinic Core

> Sigurnosna napomena: zadani korisnik, lozinka i lokalne Docker postavke su samo za razvoj. Prije stvarne uporabe promijenite admin lozinku, postavite jak `JWT_SECRET`, ogranicite CORS, koristite HTTPS, podesite backup PostgreSQL baze i napravite GDPR/access-control provjeru. ASTRA Clinic Core nije certificirani EMR i nije certificirani medicinski uredaj.

ASTRA Clinic Core je open-source modularna jezgra za rad klinike: naručivanje pacijenata, dnevni raspored, tijek pacijenta, API integracije, audit log, osnovni RBAC, inventar, nabava i priprema naplate.

Ovo nije puni EMR ni veliki ERP. MVP je namjerno fokusiran na operativni tijek klinike i modularnu arhitekturu za buduće medicinske module.

## Pilot status

Current stage: closed demo/pilot with demo data only.

- Do not enter real patient data.
- Real Croatian fiscalization is not implemented; current mode is noop/stub.
- Use demo seed/reset for pilot sessions:

```bash
docker compose exec backend python -m app.demo.seed
docker compose exec backend python -m app.demo.reset
```

Pilot documents:

- [ASTRA Architecture Bible](docs/ASTRA_ARCHITECTURE_BIBLE.md)
- [ASTRA Design System](docs/ASTRA_DESIGN_SYSTEM.md)
- [ASTRA Workspace Architecture](docs/ASTRA_WORKSPACE_ARCHITECTURE.md)
- [ASTRA Patient Clinical Knowledge Model](docs/ASTRA_PATIENT_CLINICAL_KNOWLEDGE_MODEL.md)
- [Patient Clinical Knowledge Layer MVP](docs/PATIENT_CLINICAL_KNOWLEDGE_LAYER_MVP.md)
- [Patient Clinical Summary MVP](docs/PATIENT_CLINICAL_SUMMARY_MVP.md)
- [Reception and Resource Scheduling](docs/RECEPTION_AND_RESOURCE_SCHEDULING.md)
- [Program 1 - ASTRA Clinical Workflow](docs/programs/PROGRAM_1_ASTRA_CLINICAL_WORKFLOW.md)
- [Program 1 Glossary](docs/programs/PROGRAM_1_GLOSSARY.md)
- [Program 1 Domain Object Mapping](docs/programs/PROGRAM_1_DOMAIN_OBJECT_MAPPING.md)
- [Program 1 Phase A - Patient Knowledge Stabilization Plan](docs/programs/PROGRAM_1_PHASE_A_PATIENT_KNOWLEDGE_STABILIZATION_PLAN.md)
- [Program 1 Review Pass 1 - Architectural Consistency Audit](docs/programs/PROGRAM_1_REVIEW_PASS_1_ARCHITECTURAL_CONSISTENCY_AUDIT.md)
- [ASTRA Readiness Model](docs/ASTRA_READINESS_MODEL.md)
- [ASTRA Operational Evidence Loop](docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md)
- [V20 Readiness Cockpit](docs/V20_READINESS_COCKPIT.md)
- [V23 Pilot Release Candidate](docs/V23_PILOT_RELEASE_CANDIDATE.md)
- [Codex Architecture Bible instructions](docs/CODEX_ARCHITECTURE_BIBLE_INSTRUCTIONS.md)
- [V19 Architecture Bible compliance gate](docs/V19_ARCHITECTURE_BIBLE_COMPLIANCE_GATE.md)
- [Pilot runbook](docs/PILOT_RUNBOOK.md)
- [Program 1 Phase A hardening audit](docs/programs/PROGRAM_1_PHASE_A_HARDENING_AUDIT.md)
- [Program 1 Open Questions Contract](docs/programs/PROGRAM_1_OPEN_QUESTIONS_CONTRACT.md)
- [Program 1 audit event naming](docs/programs/PROGRAM_1_AUDIT_EVENT_NAMING.md)
- [Program 1 Phase A regression notes](docs/programs/PROGRAM_1_PHASE_A_REGRESSION_NOTES.md)
- [Real data readiness checklist](docs/REAL_DATA_READINESS_CHECKLIST.md)
- [v0.1 pilot release checklist](docs/V0_1_PILOT_RELEASE_CHECKLIST.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)

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

Za pristup s drugog uredaja u istoj mrezi otvorite:

- Aplikacija: `http://IP-ADRESA-RACUNALA:5173`
- API: `http://IP-ADRESA-RACUNALA:8000`

Frontend po defaultu koristi isti hostname na kojem je otvoren u browseru i port `8000`, pa `localhost` nije potreban za mrezni pristup.

Početna prijava:

- E-pošta: `admin@astra.local`
- Lozinka: `astra123`

## Testovi i CI

Lokalno pokretanje provjera:

```bash
make test
```

Backend testovi koriste izoliranu testnu bazu i ne ovise o ručnom seedanju razvojne baze. GitHub Actions CI se pokreće na svaki push i pull request, pokreće migracije nad testnim PostgreSQL-om, backend pytest suite, frontend typecheck i frontend production build.

PostgreSQL integration testovi koriste `TEST_DATABASE_URL`. Lokalno se preskaču ako ta varijabla nije postavljena; u CI-ju je postavljena na testni PostgreSQL servis.

Za produkciju postavite `APP_ENV=production`, jak `JWT_SECRET`, kraći `ACCESS_TOKEN_MINUTES` i eksplicitni `CORS_ORIGINS`. Aplikacija namjerno odbija startup u produkciji ako su JWT ili CORS postavke nesigurne.

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
- Klinički dokumenti: interni/vanjski dokumenti, upload placeholder, AI extraction placeholder, liječnički pregled i source-linked sažetak pacijenta
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
