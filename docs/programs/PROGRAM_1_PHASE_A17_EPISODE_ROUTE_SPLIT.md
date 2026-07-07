# Program 1 Phase A17 - Episode Route Split

## 1. Svrha

A17 izdvaja Episode i ClinicalPlan rute iz `backend/app/api/routes/core.py` u zaseban route modul.

Ovo je iskljucivo route modularizacija i hardening granica odgovornosti. A17 ne vraca Episode-Based Care kao primarni workflow i ne siri Episode Engine.

Primarni klinicki temelj Programa 1 ostaje Patient Clinical Knowledge Layer: pregledani source-linked ClinicalDocuments, Patient Clinical Summary kao pomocni view i otvorena pitanja kao source-linked upozorenja.

## 2. Trenutni problem

Nakon A16 `core.py` jos uvijek sadrzi:

- episode CRUD/close rute
- episode appointments rutu
- ClinicalPlan generate/list/active/edit/reject/confirm rute
- episode clinical decision timeline
- episode-specific helper funkcije

Ta logika je pomijesana s preostalim search/catalog/audit rutama. To povecava rizik da buduci razvoj procita Episode Engine kao aktivni primarni workflow, iako Program 1 dokumentacija jasno kaze da Patient Clinical Knowledge dolazi prvo.

## 3. Ciljni modul

Ciljni backend modul je:

`backend/app/api/routes/episodes.py`

Taj modul smije sadrzavati:

- `GET /api/episodes`
- `POST /api/episodes`
- `GET /api/episodes/{episode_id}`
- `PATCH /api/episodes/{episode_id}`
- `POST /api/episodes/{episode_id}/close`
- `GET /api/episodes/{episode_id}/appointments`
- `GET /api/episodes/{episode_id}/clinical-plans`
- `GET /api/episodes/{episode_id}/clinical-plans/active`
- `POST /api/episodes/{episode_id}/clinical-plans/generate`
- `PATCH /api/clinical-plans/{plan_id}`
- `POST /api/clinical-plans/{plan_id}/reject`
- `POST /api/clinical-plans/{plan_id}/confirm`
- `GET /api/episodes/{episode_id}/clinical-timeline`

Episode-specific helperi takodjer pripadaju ovom modulu:

- `get_episode_or_404`
- `get_plan_or_404`
- `active_plan_for_episode`
- `pending_plan_for_episode`
- `propose_plan`
- `episode_with_count`

## 4. Zasticena semantika

A17 mora sacuvati sljedece:

- Episode Workspace ostaje experimental/deferred compatibility surface.
- Appointments bez epizode i dalje su dopusteni.
- Patient Clinical Knowledge ostaje primarni klinicki temelj.
- ClinicalPlan ostaje episode-bound suggestion/confirmation objekt, ne Workflow Engine.
- AI plan suggestion ostaje placeholder logika.
- Lijecnicka potvrda je obavezna prije nego plan postane aktivan i prije nego epizoda bude azurirana planom.
- Clinical decision timeline ostaje citljiv prikaz audit dogadjaja, ne Outcome Evidence objekt.
- Ne uvodi se Task engine.

## 5. Izvan scopea

A17 ne uvodi:

- novi episode lifecycle
- Task objekt
- Clinical Readiness Gate
- Episode-Based Care reaktivaciju
- workflow automatizaciju
- Outcome Evidence objekt
- novi AI provider
- novi OCR provider
- migracije baze
- stvarne podatke pacijenata
- produkcijske ili certifikacijske tvrdnje

## 6. Ocekivani ishod

Korisnik ne bi smio primijetiti funkcionalnu promjenu. Postojece API adrese, permissioni, response schema i audit dogadjaji moraju ostati kompatibilni.

Arhitektonska korist je jasnija granica: epizode i klinicki planovi ostaju izolirani compatibility/deferred route modul, a `core.py` se dalje smanjuje prema A18 razdvajanju catalog/search/audit ruta.
