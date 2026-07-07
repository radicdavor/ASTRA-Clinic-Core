# Program 1 Phase B2 - Clinical Readiness Preview Data Contract

Status: documentation-only data contract

## 1. Svrha

Ovaj dokument definira kako buduci read-only Clinical Readiness Preview smije derivirati iteme iz postojecih podataka.

Ne implementira derivaciju, template engine, API, UI ili bazu.

## 2. Data inputs

Allowed future inputs:

- Appointment
- Patient
- Service
- Provider
- Room
- reviewed ClinicalDocuments
- Patient Clinical Knowledge
- Open Questions
- Clinical Evidence Timeline as audit context
- inventory/material availability
- reception/admin human attestation
- nurse human attestation
- future consent record
- future specialty readiness templates

Input ne znaci automatsku odluku. Svaki input mora biti prikazan kroz source/evidence semantics iz B1.

## 3. Forbidden inputs

Forbidden for official preview items:

- unreviewed AI extraction
- draft ClinicalDocument
- rejected ClinicalDocument
- superseded ClinicalDocument
- Patient Clinical Summary alone
- unreviewed patient-uploaded text
- free text note without source
- AI suggestion without source/review
- ClinicalPlan as readiness source
- Episode as required anchor

Ako neki zabranjeni input postoji, smije se prikazati samo kao limitation ili pending review signal, nikada kao official source fact.

## 4. Item generation principles

Buduca item generacija mora biti:

- deterministic template-based first
- bez clinical reasoning enginea
- bez autonomous AI
- bez automatic blockers from AI
- bez task creation
- bez episode requirementa
- reviewed source-only za clinical evidence items
- jasno oznacena kao preview

Prva verzija ne smije izvoditi nove medicinske zakljucke. Smije samo pokazati da nesto treba pregledati, potvrditi ili povezati s izvorom.

## 5. Template direction

Buduci readiness templates mogu biti service-based.

Primjeri:

- gastroscopy
- colonoscopy
- H. pylori treatment/test-of-cure
- injectable aesthetic treatment
- energy-based aesthetic treatment

Templates trebaju generirati moguce readiness iteme, ne odluke.

Template smije reci:

`Provjeri postoji li pristanak za sedaciju.`

Template ne smije reci:

`Postupak je siguran.`

## 6. Limitations field

Buduci response treba ukljuciti `limitations` kada preview nema dovoljno konteksta ili kada je njegov scope ogranicen.

Primjeri:

- `Nema definiranog readiness templatea za ovu uslugu.`
- `Nema pregledanih klinickih dokumenata.`
- `Open Questions postoje, ali nisu automatski blocker.`
- `Ovo je demo/pilot preview i nije produkcijska odluka.`
- `Patient Clinical Summary nije koristen kao source of truth.`
- `AI prijedlozi bez pregleda nisu koristeni kao sluzbeni izvor.`

Limitations nisu error same po sebi. One su sigurnosni dio previewa.

