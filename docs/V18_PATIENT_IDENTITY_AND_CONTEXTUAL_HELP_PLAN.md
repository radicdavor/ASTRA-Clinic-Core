# ASTRA Clinic Core — v18 Patient Identity and Contextual Help Plan

Datum: 2026-07-05
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Zašto ovaj dokument postoji

Nakon neformalnog human walkthrougha pojavio se prvi stvarni, konkretni product feedback koji nije samo procesni:

1. Gumbi tipa **Novi**, **Dodaj**, **Spremi**, **Izdaj**, **Zaprimi** trebaju imati pomoćni hover/popover kontekst.
2. Kod **Novi pacijent** treba postojati hover/help prozor koji objašnjava što se upisuje i zašto.
3. Kod **Dodaj termin / Novi termin** pacijent se ne smije birati samo iz običnog dropdowna; treba unositi ime i prezime uz automatski search postojeće baze pacijenata.
4. Treba dodati **OIB** kao drugi jedinstveni identifikator pacijenta.
5. Kod ugovaranja termina i upisa nove usluge treba prikazivati pomoćni kontekst gdje god je primjenjivo.

Ovo je kvalitetan feedback jer dolazi iz stvarnog korištenja, ne iz apstraktne arhitekture.

Moj stav: **ovo nije feature-sprawl. Ovo je core usability i patient-identity hardening.**

Zato je opravdano napraviti ciljanu iznimku od development pause pravila: ovaj sprint treba adresirati upravo taj feedback, ali bez širenja modula, AI recepcionara, integracija ili produkcijskih real-data tvrdnji.

## 2. Kritički osvrt na trenutno stanje repozitorija

### 2.1 Patient model nema OIB ni drugi formalni identifikator

`Patient` trenutno ima:

- first_name
- last_name
- date_of_birth
- email
- phone
- notes

To je dovoljno za demo, ali nije dovoljno ni za ozbiljan pilot u hrvatskom kontekstu. Ime i prezime nisu jedinstveni. Telefon/email mogu nedostajati ili se promijeniti. Datum rođenja pomaže, ali OIB je prirodan sekundarni jedinstveni identifikator.

Ne treba forsirati OIB za sve demo slučajeve, ali treba ga podržati kao unique nullable field.

### 2.2 PatientForm je previše sirov

`PatientForm.tsx` trenutno renderira generičku listu inputa i gumb “Spremi pacijenta”. Nema:

- OIB
- objašnjenje zašto se OIB unosi
- upozorenje da se u demo modu ne unose stvarni OIB-i
- field-level help
- save help/confirmation context
- duplicate warning

Za demo i pilot to je P2 usability problem, a za real-data readiness bi postao P1/P0 ako bi korisnik unosio stvarne osobne podatke bez jasne kontrole.

### 2.3 AppointmentForm ima slab patient selection workflow

`AppointmentForm.tsx` trenutno učitava sve pacijente i nudi ih u `<select>` elementu.

To je prihvatljivo za 5 demo pacijenata, ali nije skalabilno i nije prirodno za recepciju. U stvarnom workflowu korisnik upisuje:

- ime
- prezime
- datum rođenja ili OIB ako treba razriješiti duplikat

A sustav treba ponuditi postojeće pacijente.

Trenutni dropdown stvara probleme:

- teško je pronaći pacijenta u većoj bazi
- ne vidi se dovoljno podataka za disambiguation
- ne potiče provjeru identiteta
- ne pomaže kad pacijent ne postoji

### 2.4 Contextual help / hover nije sustavno riješen

Aplikacija već ima dosta workflowa, ali gumbi nose veliku domensku težinu:

- “Završi uz potrošnju” mijenja status termina i skida zalihu
- “Izdaj račun” zaključava račun i pokreće fiscalization boundary
- “Evidentiraj uplatu” mijenja payment status
- “Potvrdi zaprimanje” mijenja zalihe
- “Kreiraj API ključ” generira secret

Takvi gumbi moraju imati pomoćni kontekst. Ne samo hover za desktop, nego i focus/click help za accessibility i touch uređaje.

### 2.5 Service selection treba više konteksta

Kod termina, usluga nije samo label. Usluga nosi:

- trajanje
- cijenu
- module
- moguće material templates
- očekivani workflow

Zato kod odabira usluge treba prikazati context panel ili popover:

- trajanje
- cijena
- što se obično radi
- eventualni materijali ako postoje
- napomena da termin može imati material consumption kasnije

## 3. Product odluka

Ovaj feedback treba tretirati kao **P2 usability + domain identity hardening**.

Nije P0/P1 jer ne ruši trenutni demo flow, ali je dovoljno važan da uđe prije širenja na nove module.

Prioritet:

1. OIB kao nullable unique patient field
2. patient search/disambiguation u appointment formu
3. contextual help/popover komponenta
4. primjena contextual helpa na Novi/Dodaj/Spremi/Izdaj/Zaprimi workflowe
5. service selection context
6. testovi
7. documentation update

## 4. UX princip: ne hover-only

Korisnik je rekao “hover prozor”. To je dobar naziv intuitivno, ali implementacija ne smije biti samo CSS hover jer:

- touch uređaji nemaju hover
- keyboard korisnici trebaju focus
- accessibility treba aria-describedby ili button-triggered popover
- kritične akcije trebaju vidljiv context i/ili confirmation

Zato implementirati komponentu:

`HelpHint` ili `ContextHelp`

Ponašanje:

- desktop: hover i focus prikazuju kratku pomoć
- mobile/touch: klik na `?` prikazuje pomoć
- keyboard: focusable trigger
- critical action: help + confirmation ako mijenja stanje

## 5. Patient identity model

### 5.1 Dodati OIB

Backend:

`Patient` model:

```python
oib: Mapped[str | None] = mapped_column(String(11), unique=True, index=True)
```

Dodati migraciju.

Dodati u schemas:

- PatientCreate
- PatientUpdate
- PatientOut

Validacija:

- optional / nullable
- ako postoji, 11 znamenki
- whitespace trim
- unique ako nije null

Za demo mode:

- ne tražiti stvarni OIB
- placeholder: “Demo OIB ili ostaviti prazno”
- banner već upozorava da nema realnih podataka

### 5.2 OIB nije zamjena za oprez

OIB je drugi jedinstveni broj, ali aplikacija mora i dalje prikazati:

- ime
- prezime
- datum rođenja
- telefon/email

Kod pronalaska pacijenta prikazati dovoljno informacija da korisnik odabere pravog pacijenta.

## 6. Patient search/disambiguation workflow za AppointmentForm

### 6.1 Novi način odabira pacijenta

Umjesto select liste:

- input: “Ime i prezime pacijenta”
- dok se tipka, pozvati `/api/patients?q=` ili novi endpoint
- prikazati rezultate
- rezultat prikazuje:
  - Ime Prezime
  - datum rođenja
  - OIB ako postoji
  - telefon/email ako postoji
- klik na rezultat postavlja `patient_id`
- prikazati selected patient card

### 6.2 Kada nema rezultata

Ako nema rezultata:

- prikazati “Nema pronađenog pacijenta”
- gumb “Kreiraj novog pacijenta”
- opcionalno prefill first_name/last_name iz upisa

Za sada ne mora biti full inline patient create, ali treba biti jasan link prema `/patients/new` s query params ili state ako je izvedivo.

### 6.3 Duplikati

Ako ima više pacijenata s istim imenom/prezimenom:

- prikazati “Pronađeno više pacijenata — provjerite datum rođenja/OIB”
- ne dopustiti submit dok korisnik ne odabere konkretnog pacijenta

### 6.4 OIB search

Search input može tražiti i po OIB-u.

Backend `list_patients(q=...)` treba pretraživati:

- first_name
- last_name
- phone
- email
- oib

## 7. Service selection context

Kod odabira usluge u AppointmentFormu:

- select ili searchable select može ostati za sada
- nakon odabira prikazati service card:
  - naziv
  - trajanje
  - cijena
  - module ako postoji
  - napomena: “Materijali se skidaju pri završetku termina ako usluga ima predložak potrošnje.”

HelpHint kod “Usluga”:

> Odaberite uslugu koja određuje trajanje, cijenu i eventualne predloške potrošnje materijala. Ako usluga nije u katalogu, prvo je dodajte u katalog usluga.

## 8. Contextual help standard

### 8.1 Gdje primijeniti odmah

Obavezno:

- Novi pacijent
- Spremi pacijenta
- Novi termin
- Pacijent search u terminu
- Usluga u terminu
- Spremi termin
- Završi uz potrošnju
- Kreiraj nacrt računa
- Izdaj račun
- Evidentiraj uplatu
- Potvrdi zaprimanje
- Kreiraj API ključ
- Deaktiviraj API ključ

### 8.2 Primjeri tekstova

#### Novi pacijent

> Otvara unos novog pacijenta. U demo načinu ne unosite stvarne osobne podatke. Za stvarni rad potrebno je provjeriti identitet pacijenta i pravila obrade podataka.

#### OIB

> OIB je dodatni jedinstveni identifikator pacijenta. U demo načinu ostavite prazno ili koristite izmišljeni demo broj. Ne unosite stvarni OIB dok real-data readiness nije odobren.

#### Novi termin

> Termin povezuje pacijenta, uslugu, liječnika, sobu i vrijeme. Sustav provjerava preklapanje liječnika i sobe.

#### Pacijent u terminu

> Počnite upisivati ime, prezime ili OIB. Ako postoji više sličnih pacijenata, provjerite datum rođenja i OIB prije odabira.

#### Usluga

> Usluga određuje trajanje, cijenu i eventualne materijale koji se mogu skinuti sa zalihe nakon završetka termina.

#### Izdaj račun

> Izdavanje zaključava draft račun i dodjeljuje službeni broj. Trenutna fiskalizacija je demo/noop i nije stvarna hrvatska fiskalizacija.

#### Zaprimanje narudžbenice

> Zaprimanje povećava zalihu i stvara skladišno kretanje. Provjerite količinu, LOT, rok i lokaciju prije potvrde.

#### API ključ

> API ključ može koristiti vanjski sustav ili AI agent. Dodijelite najmanji potreban skup scopeova. Sirovi ključ se prikazuje samo jednom.

## 9. Backend requirements

### 9.1 Patient OIB

- Add nullable `oib` to Patient.
- Add unique index where possible.
- Migration.
- Schemas update.
- Tests:
  - create patient without OIB
  - create patient with valid OIB
  - reject invalid OIB length/format
  - reject duplicate OIB
  - search by OIB

### 9.2 Patient search endpoint

Can extend existing:

`GET /api/patients?q=`

or add:

`GET /api/patients/search?q=`

Return `PatientOut[]`.

Must include OIB in PatientOut.

Do not expose sensitive fields beyond what PatientOut already allows.

### 9.3 Appointment create remains patient_id based

Do not create ambiguous appointments by free text.

Appointment create still requires a resolved `patient_id`.

Frontend search only helps choose the correct patient.

## 10. Frontend requirements

### 10.1 Add HelpHint component

Create:

`frontend/src/components/HelpHint.tsx`

Features:

- icon or `?`
- accessible label
- hover/focus display
- click toggle for touch
- accepts `title` and `children`
- no external dependency required

### 10.2 Use HelpHint in forms and critical buttons

At minimum:

- PatientForm
- AppointmentForm
- Dashboard material completion button
- AppointmentDetail material completion
- PurchaseOrders receive button
- Invoices issue/payment buttons
- ApiKeys create/deactivate

### 10.3 AppointmentForm patient search

Replace patient select with:

- text input
- filtered result list
- selected patient card
- clear selection button
- no submit until patient selected
- duplicate warning when multiple similar results

### 10.4 PatientForm OIB

Add field:

- OIB
- placeholder in demo mode
- HelpHint
- validation message if not 11 digits when present

## 11. Testing requirements

Backend tests:

- OIB create/update/search
- duplicate OIB conflict
- invalid OIB validation
- PatientOut includes OIB

Frontend smoke/static tests:

- PatientForm includes OIB
- PatientForm includes HelpHint or OIB help text
- AppointmentForm no longer relies only on select patient dropdown
- AppointmentForm includes patient search text
- AppointmentForm includes service context/help
- critical button help text present

Optional frontend interaction test:

- type patient name and select result
- submit disabled until selected

## 12. Documentation requirements

Update:

- `docs/REAL_DATA_READINESS_CHECKLIST.md` with OIB handling note
- `docs/PILOT_RUNBOOK.md` with patient search/OIB note
- `docs/KNOWN_LIMITATIONS.md` if OIB is demo-only before real-data readiness
- `docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md` to mark this feedback as P2 usability/domain hardening

## 13. Release decision impact

This feedback does **not** automatically block `v0.1-pilot` unless:

- patient selection is unusable in pilot
- user creates appointment for wrong patient
- user thinks real OIB should be entered in demo mode

If implemented before tag, it improves pilot quality.

If not implemented before tag, document as P2 limitation:

> Patient search and OIB support are planned; current demo workflow uses simplified patient selection.

## 14. V18 Codex Master Prompt

```text
You are a senior full-stack developer and healthcare UX/domain-safety engineer.

You are working on radicdavor/ASTRA-Clinic-Core.

A human walkthrough produced concrete product feedback:

1. Buttons such as Novi, Dodaj, Spremi, Izdaj, Zaprimi should show contextual help/popover where appropriate.
2. Novi pacijent should have help explaining patient creation and demo-data caution.
3. Appointment creation should not rely on a raw patient select list; user should type patient first/last name and search existing patients.
4. Add OIB as a second unique patient identifier.
5. Service selection should show helpful context when booking appointments.

This is a targeted usability/domain hardening sprint. It is allowed because it comes from pilot feedback. Do not expand clinical modules, AI automations, integrations, real fiscalization or real-data enablement.

Sprint name:

Patient Identity and Contextual Help Sprint

Non-negotiable rules:
- Keep real patient data forbidden.
- Keep demo banner and real-data warnings.
- Do not imply real Croatian fiscalization.
- Do not add broad new features.
- Appointment create must still use resolved patient_id, not ambiguous free text.
- OIB must be optional until real-data readiness is formally approved.

Phase 1 — Add OIB to Patient model

Backend:
- Add nullable `oib` field to Patient.
- Add unique index/constraint for non-null OIB if feasible.
- Add Alembic migration.
- Update PatientCreate, PatientUpdate, PatientOut.
- Validate OIB if present: exactly 11 digits.
- Trim whitespace.
- Reject duplicate OIB with 409 or validation error.

Tests:
- create without OIB succeeds
- create with valid OIB succeeds
- invalid OIB rejected
- duplicate OIB rejected
- search by OIB works
- PatientOut includes OIB

Phase 2 — Extend patient search

Update existing `/api/patients?q=` search to include OIB.

Search fields:
- first_name
- last_name
- email
- phone
- oib

Return PatientOut.

Phase 3 — Add HelpHint component

Frontend:

Create:

frontend/src/components/HelpHint.tsx

Requirements:
- accessible `?` help trigger
- hover and focus support
- click/tap support
- accepts title and body
- usable inside labels and next to buttons
- no heavy dependency

Phase 4 — PatientForm OIB and contextual help

Update PatientForm:
- add OIB field
- add HelpHint for Novi pacijent header
- add HelpHint for OIB
- add HelpHint for Spremi pacijenta
- show demo warning text near OIB: do not enter real OIB in demo mode
- frontend validation for 11 digits if entered

Phase 5 — AppointmentForm patient search/disambiguation

Replace patient dropdown with search workflow:

- text input: “Ime, prezime ili OIB”
- filtered results from `/api/patients?q=`
- result card shows name, date of birth, OIB, phone/email
- clicking result sets patient_id
- selected patient card displayed
- clear selected patient option
- submit disabled until patient selected
- if multiple similar matches, show warning: verify date of birth/OIB
- if no match, show link/button to create new patient

Do not auto-create patient in appointment form in this sprint unless very simple and safe. Prefer link to PatientForm.

Phase 6 — Service context in AppointmentForm

After selecting service, show service context card:
- service name
- duration
- price
- code if present
- module if present
- note that material templates may apply at appointment completion

Add HelpHint next to service selection.

Phase 7 — Contextual help on critical actions

Add HelpHint or accessible help text for:
- Novi pacijent
- Spremi pacijenta
- Novi termin
- Spremi termin
- Završi uz potrošnju
- Kreiraj nacrt računa
- Izdaj račun
- Evidentiraj uplatu
- Potvrdi zaprimanje
- Kreiraj API ključ
- Deaktiviraj API ključ

Do not clutter UI; use concise help.

Phase 8 — Tests and smoke checks

Backend tests:
- OIB validation/search/duplicate

Frontend smoke:
- PatientForm contains OIB
- AppointmentForm contains patient search input
- HelpHint component exists
- Invoices still show demo fiscalization warning
- ApiKeys still show dangerous scope confirmation

Phase 9 — Documentation updates

Update:
- docs/REAL_DATA_READINESS_CHECKLIST.md with OIB caution
- docs/PILOT_RUNBOOK.md with patient search/OIB step
- docs/pilot_sessions/2026-07-05_human_pilot_01_triage.md with this feedback as P2 usability/domain hardening
- docs/V0_1_GO_NO_GO_MATRIX.md if needed

Suggested commit sequence:
1. feat: add optional patient OIB field and validation
2. test: cover patient OIB validation and search
3. feat: add contextual help component
4. feat: add OIB and help to patient form
5. feat: add patient search selection to appointment form
6. feat: add service context help to appointment form
7. feat: add help hints to critical workflow actions
8. test: update frontend smoke for help and patient search
9. docs: document OIB and patient identity workflow

Definition of done:
- OIB supported as optional unique patient identifier
- appointment form searches patients by name/OIB
- user must select a resolved patient before creating appointment
- contextual help exists for key Novi/Dodaj/Spremi/Izdaj/Zaprimi actions
- demo mode still warns against real patient/OIB data
- backend and smoke tests updated
```

## 15. What not to do in this sprint

Do not:

- implement full patient merge
- implement national OIB verification service
- require OIB for all patients
- enable real patient data
- add patient portal
- add EMR charting
- add AI receptionist
- add external integrations

## 16. Final recommendation

This is the right kind of next work because it comes from usage friction.

It improves the core operational loop without expanding the product in a speculative direction.

Implement this before broadening modules.
