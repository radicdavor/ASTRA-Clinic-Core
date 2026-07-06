# ASTRA Clinic Core — Post v0.1 Architectural Roadmap

Datum: 2026-07-06
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak

ASTRA Clinic Core je nakon V23 došla do prve velike prekretnice.

V23 definira `v0.1-pilot` release candidate i eksplicitno ne stvara tag bez maintainer odluke. To je ispravno.

Nakon `v0.1-pilot` više nije zdravo nastaviti beskonačno s V24, V25, V26 sprintovima koji dodaju po jedan sloj.

Projekt sada treba prijeći na razvoj kroz **arhitektonske programe**.

Predloženi redoslijed:

1. ASTRA Episode Engine
2. ASTRA Workflow Engine
3. ASTRA Knowledge Engine
4. Clinical Module SDK
5. Gastroenterology Suite v1
6. ASTRA AI Operating Layer

Ovaj dokument definira taj prijelaz i prvi veliki program: **Episode Engine**.

## 2. Zašto mijenjati ritam razvoja

Dosadašnji V1–V23 sprintovi bili su korisni jer su izgradili temelj:

- pacijente
- termine
- usluge
- račune
- inventar
- nabavu
- audit
- API ključeve
- readiness cockpit
- workspace arhitekturu
- pilot/release governance
- design system
- operational evidence loop

Ali sada projekt ima dovoljno širine.

Sljedeći rizik nije manjak funkcija.

Sljedeći rizik je da se funkcije počnu gomilati bez novog domenskog centra.

Taj novi domenski centar treba biti:

> Clinical Episode

## 3. Zašto Episode Engine prije Workflow Enginea

Workflow Engine bez Clinical Episode objekta postaje samo lista taskova.

Episode Engine daje kontekst:

- zašto se termin dogodio
- kojoj kliničkoj priči pripada
- koji su nalazi povezani
- koji su računi povezani
- koja je kontrola planirana
- što je otvoreno
- što je završeno

Primjer:

Pacijent može imati:

- epizodu GERB/refluks
- epizodu polip debelog crijeva
- epizodu H. pylori eradikacije
- epizodu estetskog tretmana
- epizodu kontrole debljine/metabolizma

Termini bez epizode su samo događaji.

Termini unutar epizode postaju priča.

## 4. Što je Clinical Episode

Clinical Episode je vremenski i klinički okvir oko jednog problema, cilja ili terapijskog procesa.

Epizoda nije isto što i termin.

Termin je događaj.

Epizoda je kontekst.

Epizoda može sadržavati:

- jedan ili više termina
- nalaze
- račune
- materijalne potrošnje
- dokumente
- zadatke
- follow-up plan
- status
- audit

## 5. Minimalni Episode model

Za prvi MVP ne treba graditi puni EMR.

Minimalni model:

- id
- patient_id
- title
- episode_type
- status
- priority
- start_date
- end_date
- summary
- clinical_notes
- owner_provider_id
- created_by
- created_at
- updated_at

Predloženi statusi:

- open
- active
- waiting
- completed
- cancelled
- archived

Predloženi episode_type:

- general
- gastroenterology
- endoscopy
- dermatology_aesthetics
- metabolic
- preventive
- administrative

Za početak episode_type neka bude string/enum-like field, ne zaseban kompleksan module engine.

## 6. Relacije

Prva faza:

- Patient 1:N ClinicalEpisode
- ClinicalEpisode 1:N Appointment

Dodati nullable `episode_id` na Appointment.

Ne treba odmah povezivati sve objekte.

Druga faza:

- Invoice optional episode_id
- StockMovement optional episode_id kroz appointment ili direktno
- Document optional episode_id kad dokumenti postoje
- Task optional episode_id kad Workflow Engine dođe

## 7. Patient Workspace nakon Episode Enginea

Patient Workspace treba dobiti novu sekciju:

**Epizode**

Prikaz:

- active/open epizode na vrhu
- status
- tip
- zadnji termin
- sljedeći termin
- broj povezanih termina
- kratki summary

Patient Workspace postaje:

- identitet
- epizode
- termini
- računi
- audit

Epizode trebaju biti prvi klinički sloj iznad termina.

## 8. Episode Workspace

Dodati novu rutu:

`/episodes/:id`

Episode Workspace treba prikazati:

- episode header
- patient identity
- episode status
- episode type
- start/end date
- owner provider
- summary
- clinical notes
- related appointments
- related invoices ako postoji endpoint ili deferred
- audit timeline
- actions:
  - update episode
  - add appointment to episode
  - close episode

Ne graditi dokumente, task engine ili AI još.

## 9. Appointment integration

AppointmentForm treba omogućiti:

- nakon odabira pacijenta, prikaz aktivnih epizoda tog pacijenta
- odabir postojeće epizode
- opciju “bez epizode”
- link “nova epizoda” ako pacijent nema odgovarajuću

AppointmentDetail treba prikazati:

- episode link ako postoji
- warning ako termin nema epizodu, ali je klinički relevantan

Ne blokirati sve termine bez epizode u prvoj verziji.

Za demo/pilot neka episode bude optional.

## 10. Readiness integration

Readiness treba dobiti check:

- key: `clinical_episodes`
- label: `Kliničke epizode`
- status:
  - ok ako postoje aktivne epizode ili ako demo još nema episode requirement
  - warning ako postoje termini bez episode_id
- decision_impact: review
- target_path: `/patients` ili budući `/episodes`

Ne blokirati demo ako epizode nisu potpune.

## 11. Audit

Audit mora pratiti:

- create ClinicalEpisode
- update ClinicalEpisode
- close ClinicalEpisode
- appointment linked to episode
- appointment unlinked from episode

Audit summary mora biti čitljiv.

## 12. API design

Minimalni endpointi:

- `GET /api/episodes`
- `POST /api/episodes`
- `GET /api/episodes/{id}`
- `PATCH /api/episodes/{id}`
- `GET /api/patients/{patient_id}/episodes`
- `GET /api/episodes/{id}/appointments`

Optional:

- `POST /api/episodes/{id}/close`

Permissions:

- `episodes.read`
- `episodes.write`

Seed roles should include appropriate permissions for admin/physician.

## 13. Frontend pages

Add:

- `Episodes.tsx` list page
- `EpisodeForm.tsx`
- `EpisodeDetail.tsx` workspace

Routes:

- `/episodes`
- `/episodes/new`
- `/episodes/:id`

Navigation:

- add `Epizode` to AppShell nav
- Patient Workspace links to episodes
- AppointmentDetail links to episode

## 14. Tests

Backend tests:

- create episode
- update episode
- close episode
- list patient episodes
- link appointment to episode
- filter/list episode appointments
- audit create/update/close
- permissions for episode read/write

Frontend smoke:

- `/episodes` route exists
- EpisodeDetail exists
- PatientDetail includes Epizode
- AppointmentForm includes episode selection after patient selected
- AppointmentDetail links to episode when present

## 15. What not to build yet

Do not build:

- complex clinical guideline engine
- task engine
- knowledge engine
- documents
- lab integration
- AI episode summarization
- automatic diagnosis coding
- billing rules by episode
- real-data production rules

Episode Engine MVP is a structural layer, not a full EMR.

## 16. Release impact

Episode Engine should be post-`v0.1-pilot` work.

If implemented before tag, it must not block `v0.1-pilot` unless it breaks existing pilot flow.

If implemented after tag, it becomes the first architectural program toward alpha.

## 17. Development rule

Every new large capability after `v0.1-pilot` must answer:

> Does this strengthen ASTRA as a clinic operating system, or is it just another feature?

Episode Engine strengthens the operating system.

That is why it is first.

## 18. Implementation status

Episode Engine Foundation is now implemented as the first post-v0.1 architectural program.

Implemented scope:

- `ClinicalEpisode` backend model
- optional `Appointment.episode_id`
- episode API endpoints
- patient/appointment validation for episode linking
- episode audit events
- `ClinicalPlan` model
- AI Assisted Clinical Plan proposal/review/confirm flow
- clinical decision timeline
- `/episodes`, `/episodes/new` and `/episodes/:id`
- Patient Workspace episode tab
- Appointment form episode selection
- Appointment Workspace episode context/warning
- readiness check `clinical_episodes`
- demo seed episodes
- `docs/ASTRA_CLINICAL_MODEL.md`
- `docs/EPISODE_ENGINE_MVP.md`
- `docs/AI_ASSISTED_CLINICAL_PLAN_MVP.md`

Still deliberately deferred:

- Workflow Engine
- Knowledge Engine
- autonomous AI automation
- real AI provider integration
- new clinical modules
- documents/labs/prescriptions
- real-data approval
- real Croatian fiscalization
