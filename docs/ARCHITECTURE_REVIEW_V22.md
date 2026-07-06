# ASTRA Clinic Core — Architecture Review v22

Datum: 2026-07-06
Repozitorij: `radicdavor/ASTRA-Clinic-Core`

## 1. Sažetak

Repozitorij je sada u znatno zrelijoj fazi nego prije nekoliko sprintova. ASTRA više nije samo backend MVP s ekranima. Sada ima:

- Architecture Bible
- Design System
- Workspace Architecture
- Readiness Model
- Patient Workspace
- Appointment Workspace smjer
- Readiness Cockpit
- ActionButton i HelpHint standard
- OIB i patient identity helper
- possible duplicate patient endpoint
- pilot smoke checks
- release/pilot governance dokumente

Moj kritički stav: **projekt je jako napredovao, ali sada je najveći rizik fragmentacija governance slojeva.**

Imamo više dobrih koncepata:

- readiness
- workspace
- design system
- pilot evidence
- release gate
- audit
- ActionButton/HelpHint

Ali oni još nisu potpuno spojeni u jedan operativni ciklus:

> Readiness problem → ciljano otvaranje workspacea → korisnička akcija → audit → readiness update → pilot/release evidence.

V22 ne smije dodavati novu širinu. V22 mora zatvoriti taj krug.

## 2. Što je dobro

### 2.1 Architecture Bible postoji i ima ispravan autoritet

`docs/ASTRA_ARCHITECTURE_BIBLE.md` već definira temeljnu filozofiju:

- čovjek iznad softvera
- jedan izvor istine
- jedan jezik
- modularnost
- API first
- AI je suradnik
- audit svega važnog

To je vrlo dobra osnova.

### 2.2 Design System sada postoji

`docs/ASTRA_DESIGN_SYSTEM.md` definira:

- akcijske kategorije
- standardne glagole
- HelpHint pravila
- confirmation pravila
- patient identity display
- demo/fiscalization warning language
- AI label language

To je važan pomak. ASTRA sada ima početak jezika proizvoda.

### 2.3 ActionButton postoji

`frontend/src/components/ActionButton.tsx` uvodi zajednički pattern za akcije:

- variant
- HelpHint
- confirmation
- submit/button mode

To je točan smjer. Ali sada treba paziti da ne ostane samo djelomično korištena komponenta.

### 2.4 Patient identity je značajno bolji

Pacijent sada ima OIB u modelu i shemama, patient search uključuje OIB, a frontend ima `patientIdentity` helper. To je važan domenski napredak.

Također postoji `possible-duplicates` endpoint. To još nije full patient merge, ali je dobar MVP za sigurniji unos.

### 2.5 Workspace Architecture je pokrenuta

`docs/ASTRA_WORKSPACE_ARCHITECTURE.md` definira workspace principe, a Patient Workspace postoji na `/patients/:id`.

Patient Workspace sada prikazuje:

- identitet
- OIB
- termine
- račune
- audit
- moguće duplikate
- akciju za novi termin

To je puno zreliji model od običnog PatientDetail ekrana.

### 2.6 Readiness Cockpit je stvarno koristan

`/api/readiness` i `/readiness` daju pregled demo sigurnosti, fiskalizacije, core podataka, audita, zalihe, računa i API ključeva.

To je jako korisno prije svakog demo/pilot prolaza.

### 2.7 Frontend smoke je praktičan guard

`frontend/scripts/pilot-smoke.mjs` provjerava prisutnost ključnih ekrana, ruta, komponenti i sigurnosnih tekstova. To nije pravi E2E, ali je koristan statički safety net.

## 3. Najvažnije slabosti

### 3.1 Readiness još ne zatvara cijeli operativni krug

Readiness Cockpit kaže što treba provjeriti, ali mora još jače voditi korisnika prema sljedećoj akciji.

Ako readiness kaže:

- niska zaliha
- unpaid invoices
- API keys
- audit missing

korisnik treba odmah znati:

- gdje kliknuti
- što provjeriti
- je li to blocker ili warning
- kako to utječe na v0.1 pilot gate

V21 je počeo tražiti target links; V22 treba dovršiti “risk-to-action” model.

### 3.2 Readiness status nije dovoljno povezan s release gateom

Readiness `blocked` i release `No-Go` nisu isto, ali su povezani. To treba jasno modelirati.

Primjer:

- noop fiscalization = warning, ne blocker za demo
- real_data_allowed=true u demo modu = critical/blocker
- active API keys = warning, ali može postati blocker ako imaju dangerous scopes
- human pilot evidence missing = warning ili release blocker ovisno o fazi

Treba formalizirati mapiranje:

`ReadinessCheck.status` → `Pilot decision impact`.

### 3.3 Patient Workspace je dobar, ali nije još “clinical narrative”

Patient Workspace prikazuje povezane objekte, ali još nema narativ:

- što je posljednje bilo
- što je sljedeće
- što je otvoreno
- što zahtijeva pažnju

Za clinic OS, Patient Workspace mora s vremenom postati “patient command center”, ne samo zbir tablica.

V22 ne treba graditi sve, ali treba definirati `Patient Summary Strip` i `Next Action` pattern.

### 3.4 Invoice ostaje slabiji workspace kandidat

Invoice UI ima dosta funkcija, ali još nije pravi object workspace. V21 je tražio `INVOICE_WORKSPACE_PROPOSAL`. To treba držati kao sljedeći fokus nakon readiness/workspace konvergencije.

### 3.5 Audit timeline je prisutan, ali nije pretvoren u objašnjivu povijest

Audit trenutno dokazuje da se nešto dogodilo. Sljedeća razina je da korisnik može razumjeti što se dogodilo.

Potrebno je:

- human readable action labels
- actor labels
- entity links
- before/after diff kao sažetak

Ne kao veliki feature, nego kao standard za workspace audit panel.

### 3.6 Static smoke nije dovoljan dugoročno

`pilot-smoke.mjs` čuva važne stringove. Dobro. Ali sada kad postoji Readiness → Workspace → Action flow, treba barem jedan minimalni browser/E2E ili API flow test koji potvrđuje navigaciju.

Ne treba odmah Playwright ako je previše. Ali treba dokumentirati odluku.

## 4. Preporučeni sljedeći sprint

Naziv:

**Operational Evidence Loop Sprint**

Cilj:

Zatvoriti krug:

`Readiness → Workspace → Action → Audit → Release evidence`

Bez novih kliničkih modula, bez novih integracija, bez real-data enablementa.

Prioriteti:

1. Readiness check target links i decision impact
2. Readiness UI kao “risk-to-action” cockpit
3. Patient Workspace summary strip
4. Workspace audit readability
5. Invoice Workspace proposal / minimal route odluka
6. Pilot runbook update: readiness-first, workspace-driven
7. Smoke/e2e guard za readiness-to-workspace navigation
8. Architecture proposal za Operational Evidence Loop

## 5. Go / No-Go za novi razvoj

Go:

- povezivanje readinessa s postojećim ekranima
- workspace UX refinement
- audit readability
- testovi
- dokumentacija

No-Go:

- novi medicinski moduli
- Google Calendar/OpenEMR
- AI receptionist
- stvarna fiskalizacija
- real patient data
- production deployment claims

## 6. Zaključak

ASTRA sada ima dobre blokove. Sljedeći korak nije dodati još blokova, nego spojiti postojeće u jedan dokazivi operativni tok.

Ako korisnik vidi problem u readiness cockpit-u, mora moći kliknuti do pravog workspacea, napraviti sigurnu akciju, vidjeti audit i znati je li pilot/release gate time bolji.

To je trenutak kad ASTRA počinje izgledati kao operativni sustav klinike, a ne samo kao zbir ekrana.
