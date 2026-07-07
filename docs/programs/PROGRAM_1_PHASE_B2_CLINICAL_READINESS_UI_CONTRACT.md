# Program 1 Phase B2 - Clinical Readiness UI Contract

Status: documentation-only UI contract

## 1. Svrha

Ovaj dokument definira buduci UI contract za read-only Clinical Readiness Preview.

Ne implementira UI, rute, komponente, tipove ili API pozive.

## 2. Target surface

Prva buduca UI povrsina treba biti:

`Appointment Workspace`

Razlog:

- appointment povezuje pacijenta, uslugu, provider, sobu i vrijeme
- clinical readiness je patient/service/procedure-specific
- Appointment Workspace je prirodno mjesto za pregled prije planiranog klinickog cina

Prva implementacija ne treba biti u:

- Readiness Cockpitu
- Patient Workspaceu kao primarnom sourceu
- Episode Workspaceu
- Receptionu kao clinical decision surfaceu

Reception kasnije smije prikazati jednostavan operativni indikator, ali ne kao prvu klinicku decision povrsinu.

## 3. UI sections

Buduca sekcija u Appointment Workspaceu:

Title:

`Klinicka spremnost - preview`

Subtitle:

`Read-only prikaz mogucih uvjeta za ovaj planirani klinicki cin. Ne donosi odluke i ne blokira postupak.`

Sekcije:

- overall readiness status
- blocking/warning items
- missing documents
- physician review items
- nurse/admin checks
- source/evidence badges
- limitations
- explanation of preview-only status

## 4. Visual rules

Buduci UI mora:

- jasno prikazati `PREVIEW` label
- jasno razlikovati Clinical Readiness od Operational Readinessa
- pokazati izvore za document-derived iteme
- pokazati ogranicenja previewa
- odvojiti warninge od dijagnoza
- odvojiti Open Questions od taskova
- prikazati missing document kao nedostajuci izvor, ne kao klinicku odluku

Buduci UI ne smije:

- prikazati zeleno `approved` dok governance ne postoji
- prikazati `AI cleared`
- prikazati `procedure allowed`
- prikazati warning kao dijagnozu
- prikazati Open Question kao task
- prikazati missing document kao final clinical decision
- sakriti source badge za document-derived item

## 5. Role-specific display

Reception/admin:

- vidi admin-check iteme
- vidi missing documents
- ne vidi ili ne clear-a physician-only clinical judgement kao svoju radnju

Nurse:

- vidi preparation/checklist iteme
- vidi sto treba nurse action
- ne moze overrideati physician-only iteme

Physician:

- vidi sve iteme
- future-only: moze confirm/override nakon sto governance postoji

AI:

- nije UI actor
- AI suggestions, ako se prikazu, moraju biti jasno oznaceni kao suggestion

## 6. Empty states

Buduci UI mora imati sigurne empty states:

- no appointment
- no service
- no reviewed sources
- no template
- preview unavailable
- demo-only warning

Primjeri poruka:

- `Preview nije dostupan jer termin nema povezanu uslugu.`
- `Nema pregledanih klinickih dokumenata za ovog pacijenta.`
- `Za ovu uslugu jos nije definiran clinical readiness template.`
- `Ovo je demo/pilot preview i nije produkcijska odluka.`

## 7. No-go UI actions

Prva buduca UI implementacija ne smije dodati:

- `Mark ready`
- `Override`
- `Create task`
- `Send to patient`
- `Close episode`
- `Proceed allowed by AI`
- `Resolve open question`

Ove akcije smiju postojati samo u buducim fazama nakon posebnog governance, role, audit i safety contracta.

