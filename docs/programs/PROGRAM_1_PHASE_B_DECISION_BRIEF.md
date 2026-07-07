# Program 1 Phase B - Decision Brief

Status: preporuka smjera, bez implementacije

## 1. Svrha

Ovaj dokument predlaze sljedecu fazu Programa 1 nakon zatvaranja Phase A.

Ne implementira novu funkcionalnost, ne uvodi nove modele, ne otvara produkciju i ne odobrava stvarne podatke pacijenata.

## 2. Recommended Phase B direction

Preporuka:

`Phase B - Clinical Readiness Design, not implementation`

Razlog:

Prije gradnje taskova, workflowa ili automatizacije epizoda, ASTRA mora definirati sto znaci da je pacijent klinicki spreman za odredeni termin, uslugu ili postupak.

Phase B treba prvo biti design/spec faza. Tek nakon odobrenog operating modela moze se odluciti hoce li i kada krenuti implementacija.

## 3. Why not Task Engine yet

Task engine jos nije pravi sljedeci korak.

Razlozi:

- Open Questions jos nemaju lifecycle, owner ili due date
- Outcome Evidence ne postoji
- Clinical Readiness Gate jos nije definiran
- taskovi bez readiness i closure semantike stvarali bi operativni sum
- taskovi trebaju nastati iz potvrdenih klinickih odluka, ne iz sirovih nerazrijesenih stavki

Ako ASTRA prerano uvede taskove, korisnici ce dobiti vise posla, a ne jasniji klinicki tok.

## 4. Why not Episode-Based Care yet

Episode Engine postoji, ali ostaje deferred.

Patient Clinical Knowledge je sada jaci temelj, ali Episode-Based Care treba pricekati dok se ne definiraju:

- clinical readiness semantics
- task lifecycle
- closure semantics
- odnos epizode prema pregledanim source dokumentima
- odnos epizode prema otvorenim pitanjima

Epizoda ne smije postati izvor klinicke istine. Ona kasnije moze organizirati pregledane cinjenice.

## 5. Why not real AI/OCR yet

Real AI/OCR nije spreman za Phase B implementaciju.

Razlozi:

- file/security pravila nisu produkcijski definirana
- real-data readiness nije odobren
- OCR moze stvoriti lazni osjecaj tocnosti ako nema stabilnog review procesa
- AI provider moze stvoriti lazni osjecaj klinicke sigurnosti ako readiness i source rules nisu formalizirani

Postojeci placeholder lifecycle dovoljan je za demo/pilot dokaz principa:

AI proposes. Physician confirms. ASTRA records both.

## 6. Phase B candidate scope

Phase B treba definirati:

- Clinical Readiness Gate model
- readiness statuse
- patient/service/procedure-specific readiness rules
- override semantics
- uloge lijecnika, medicinske sestre i administracije
- odnos prema Operational Readiness
- odnos prema ClinicalDocument evidence
- odnos prema buducem Task engineu
- gastroenteroloske primjere
- estetske medicine primjere
- no-code-first pristup, osim ako maintainer posebno odobri implementaciju

## 7. Phase B no-go

Phase B ne smije odmah implementirati:

- Task engine
- Workflow Engine
- autonomni AI
- production real-data workflows
- episode automation
- Outcome Evidence object
- patient-facing automation

## 8. Recommended next Codex task

Preporuceni sljedeci task:

`Program 1 Phase B0 - Clinical Readiness Gate Operating Model`

Ovaj task treba biti documentation-first.

Ocekivani izlaz:

- definicija Clinical Readiness Gate pojma
- razlika izmedu Operational Readiness i Clinical Readiness
- status model
- override pravila
- primjeri za gastroenterologiju i estetsku medicinu
- jasni No-Go uvjeti prije implementacije

