# Program 1 Phase B7 - Clinical Readiness Template Versioning Design

Status: design-first, demo/pilot only

## 1. Svrha

B7 definira kako Clinical Readiness templatei i njihovi bindingi trebaju biti verzionirani prije bilo kakvog DB modela, template editora ili produkcijske upotrebe.

Ovaj dokument ne uvodi:

- DB template table
- DB binding field
- Alembic migraciju
- template editor
- enforcement
- override workflow
- Task engine
- Workflow Engine
- real AI/OCR
- real patient data
- production/certification claim

Svrha je sprijeciti da se znacenje templatea ili bindinga promijeni tiho, bez traga i bez razumljivog konteksta.

## 2. Problem koji B7 rjesava

B6 je dodao demo explicit service binding prije keyword fallbacka.

To pokazuje buduci smjer, ali ostaje otvoreno:

- kako znati koja je verzija templatea koristenja u previewu
- kako razlikovati promjenu template contenta od promjene bindinga
- kako sprijeciti tiho mijenjanje povijesnog znacenja
- kako kasnije auditirati promjenu
- kako korisniku objasniti da je verzija demo/pilot, a ne produkcijsko pravilo

## 3. Template identity vs template version

Template identity i template version nisu isto.

`template_key` oznacava family ili identitet templatea:

- `gastroscopy`
- `colonoscopy`
- `hpylori`
- `aesthetic_injectable`
- `aesthetic_skinbooster_pn`
- `aesthetic_energy_device`
- `generic`

`template_version` oznacava konkretnu verziju sadrzaja templatea.

Primjer:

- `template_key="colonoscopy"`
- `template_version="demo-v1"`

Promjena naziva itema, statusa, severityja ili suggested actiona moze promijeniti interpretaciju previewa i zato u buducem modelu treba novu verziju.

## 4. Binding version vs template version

Binding version i template version nisu isto.

Template version govori:

- sto template sadrzi
- koji itemi se prikazuju
- kako su itemi klasificirani

Binding version govori:

- koja usluga koristi koji template
- tko je odobrio vezu
- zasto je promjena napravljena
- od kada vrijedi

B7 ne implementira binding version storage.

B7 samo dokumentira razlikovanje i dodaje demo template version metadata u preview.

## 5. Future conceptual fields

Buduci template version model trebao bi imati:

- template key
- template version
- active/inactive
- change reason
- author
- approver
- effective date
- retired date
- changelog

Buduci binding version model trebao bi imati:

- service id
- template key
- template version
- binding version
- binding status
- reason
- approving role/person
- effective date
- retired date
- audit entry

B7 ne uvodi te tablice.

## 6. Current demo metadata

B7 runtime smije izloziti samo staticki demo metadata:

- `template_version`
- `template_version_warning`

Za staticne templatee u kodu prva vrijednost je:

`demo-v1`

Warning:

`Template version je demo/pilot oznaka iz staticne konfiguracije; nije produkcijsko verzioniranje.`

## 7. No-Go

B7 No-Go:

- nema DB persistencea
- nema migracije
- nema template editora
- nema production versioning claim
- nema audit eventa za read-only preview
- nema retroaktivnog mijenjanja povijesnog znacenja
- nema enforcementa temeljem demo verzije
- nema AI-generated template verzije
- nema stvarnih pacijentovih podataka

Ako produkcijsko verzioniranje postane potrebno, mora biti zaseban task s migracijom, auditom, rollback planom i governance odobrenjem.

## 8. Safety

Demo version metadata je samo transparency layer.

Ne smije:

- odobriti postupak
- clearati readiness
- pretvoriti template u klinicku smjernicu
- zamijeniti lijecnicku prosudbu

ASTRA i dalje samo prikazuje i upozorava.

Lijecnik odlucuje.
