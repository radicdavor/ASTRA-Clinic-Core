# Program 1 Phase B5 - Clinical Readiness Template Governance

Status: governance design, no runtime enforcement

## 1. Svrha

Ovaj dokument definira governance za buduce Clinical Readiness template bindinge i buduce promjene templatea.

Ne uvodi:

- backend persistence
- database migraciju
- template editor
- production template rules
- enforcement
- override workflow
- Task engine
- real AI/OCR
- real-data odobrenje

Svrha je sprijeciti da demo/pilot templatei izgledaju kao nevidljiva produkcijska klinicka pravila.

## 2. Ownership

Buduci template binding ima tri konceptualna vlasnika.

### Medical owner

Medical owner je lijecnik ili medical lead koji odobrava klinicki smisao vezanja templatea na uslugu.

Odgovoran je za:

- klinicku prikladnost template familyja
- procjenu je li item label samo check/prompt, a ne medicinska direktiva
- potvrdu da template ne zamjenjuje lijecnicku prosudbu
- odobrenje promjene kada binding moze utjecati na klinicki tok

### Operational owner

Operational owner je osoba odgovorna za radni tok klinike, recepciju, sestrinski tok ili katalog usluga.

Odgovoran je za:

- prijavu da usluga nema dobar template
- provjeru da nazivi usluga u katalogu odgovaraju stvarnom toku
- prepoznavanje operativnih problema u previewu
- komunikaciju izmedu recepcije, sestre i lijecnika

Operational owner ne odobrava klinicki binding bez medical ownera.

### Technical owner

Technical owner je maintainer sustava.

Odgovoran je za:

- implementaciju konfiguracije
- migracije ako budu odobrene
- regression tests
- audit zapis buducih promjena
- rollback plan
- jasno odvajanje demo/pilot i produkcijskog ponasanja

Technical owner ne smije samostalno definirati klinicko znacenje templatea.

## 3. Who may propose binding

Reception/admin moze predloziti operational binding issue.

Primjeri:

- usluga se prikazuje s generic templateom, a trebala bi biti kolonoskopija
- naziv usluge je promijenjen pa keyword fallback vise ne radi
- template prikazuje operativno nejasnu stavku

Medicinska sestra moze predloziti sestrinski ili pripremni binding concern.

Primjeri:

- priprema crijeva nedostaje iz kolonoskopijskog previewa
- product/batch item nije prikladan za odredeni tretman

Physician/medical lead mora odobriti clinical template binding.

AI smije sugerirati kandidat templatea, ali ga ne smije vezati.

AI suggestion mora biti jasno oznacen kao prijedlog i ne smije promijeniti konfiguraciju bez ljudskog odobrenja.

## 4. Future approval rules

Buduci explicit binding mora ukljuciti:

- template key
- service id
- reason
- approving role/person
- date/time
- version
- audit entry

Dodatno je pozeljno:

- prethodni binding
- novi binding
- affected service label
- change category: new binding, correction, retirement, rollback
- link na decision note ili maintainer approval

B5 ovo ne implementira.

Bez persistencea nema formalnog binding audit eventa.

## 5. Template versioning concept

Buduci template versioning treba razlikovati template identity od template contenta.

Konceptualna polja:

- template key
- template version
- active/inactive
- change reason
- effective date
- retired date
- author/approver

Pravila:

- promjena item labela ili statusa mora dobiti novu verziju ako moze utjecati na interpretaciju previewa
- povijesni previewi ne smiju tiho mijenjati znacenje
- template version treba biti prikazan u UI-ju kada postoji
- demo/pilot staticni templatei mogu imati implicitnu development verziju, ali to nije produkcijsko versioniranje

B5 ne uvodi DB model za versioning.

## 6. Safety rules

Safety pravila:

- template changes must not silently alter historical interpretation
- preview should show template key and version when available
- production use requires formal governance outside current scope
- demo/pilot templates are not clinical guidelines
- template item labels are prompts/checks, not medical directives
- keyword fallback is not production binding
- generic fallback is not evidence of clinical readiness
- no AI-generated template binding without human approval
- no patient-specific mutation of a service template
- no enforcement until role, override, audit and governance contracts exist

Ako binding governance nije jasan, default je:

`needs_physician_review` ili read-only warning, bez workflow blokade.
