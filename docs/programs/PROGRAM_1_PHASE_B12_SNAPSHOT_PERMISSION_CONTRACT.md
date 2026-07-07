# Program 1 Phase B12 - Snapshot Permission Contract

Status: documentation-only permission contract

## 1. Svrha

B12 definira buducu permission semantiku za Clinical Readiness Snapshot capture i pregled povijesti.

Ovaj dokument nije implementacija.

Ovaj dokument ne uvodi:

- backend kod
- frontend kod
- RBAC seed promjenu
- novu permission tablicu
- capture endpoint
- snapshot UI
- DB migraciju
- produkcijsko odobrenje
- odobrenje za stvarne podatke pacijenata
- compliance ili certified EMR / medical-device claim

Svrha je prije implementacije jasno odvojiti tko smije vidjeti snapshot, tko ga smije eksplicitno captureati, tko ga smije supersedeati i sto ta ovlast nikada ne znaci.

Snapshot permission ne znaci clinical approval.

Snapshot permission ne znaci override.

Snapshot permission ne mijenja appointment status.

## 2. Buduce permissions

| Permission | Svrha | Dopustena akcija | Zabranjena akcija | Default assignment preporuka | Rizik ako je presiroko dodijeljena |
| --- | --- | --- | --- | --- | --- |
| `clinical_readiness.snapshots.read` | Pregled spremljenih snapshotova i history prikaza. | Otvoriti snapshot history i procitati immutable payload/disclaimer. | Captureati, supersedeati, editirati ili brisati snapshot. | Physician: da. Nurse: da ako sudjeluje u pripremi. Reception/admin: samo limited status ako governance odobri. AI/API: ne default. | Korisnici mogu pogresno tumaciti snapshot kao clinical approval ako UI nije jasan. |
| `clinical_readiness.snapshots.write` | Eksplicitni capture novog snapshota. | Spremiti server-side preview kao immutable snapshot uz razlog i audit. | Potvrditi spremnost, clearati warninge, stvarati task/outcome, mijenjati termin. | Physician: da za clinical-context snapshot. Nurse: samo za operational preview ako buduci governance eksplicitno dopusti. Admin/reception: ne default. AI/API/system: ne default. | Snapshot capture moze izgledati kao lijecnicka odluka ako je dostupan krivim ulogama. |
| `clinical_readiness.snapshots.supersede` | Označiti da noviji snapshot zamjenjuje stariji u prikazu historyja. | Supersedeati snapshot uz novi snapshot, razlog i audit. | Editirati payload starog snapshota ili brisati povijest. | Ograniceno na physician ili posebno ovlastenog clinic admina uz razlog. AI/API/system: ne default. | Povijest moze izgledati izmijenjeno ako supersession nije jasno auditiran. |
| `clinical_readiness.snapshots.audit_read` | Citati detaljni audit payload snapshota. | Vidjeti audit metapodatke, actor, reason, template metadata i counts. | Captureati ili mijenjati snapshot. | Physician/clinic admin: da prema governanceu. Nurse/reception: samo ako treba za operativnu kontrolu. AI/API: ne default. | Previse detalja moze izloziti klinicki kontekst osobama bez potrebe za njim. |

## 3. Role mapping

| Role | Can view snapshot? | Can capture snapshot? | Can supersede snapshot? | Can read audit payload? | Conditions | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Physician | Da, uz `clinical_readiness.snapshots.read`. | Da, uz `clinical_readiness.snapshots.write` i razlog. | Da samo uz `clinical_readiness.snapshots.supersede` i razlog. | Da, uz `clinical_readiness.snapshots.audit_read`. | Snapshot mora ostati preview-only i source-linked. | Physician capture ne znaci da je postupak odobren. |
| Nurse | Da, ako je dio pripreme pacijenta. | Ne default. Moguce samo za operational preview snapshot ako buduci governance to posebno odobri. | Ne default. | Ograniceno prema potrebi. | Mora biti jasno da nurse capture nije physician clinical approval. | Default treba biti read, ne write. |
| Reception/admin | Samo limited status/history ako governance dopusti. | Ne default. | Ne. | Ne default. | Ne smije captureati clinical-context snapshot. | Reception moze raditi raspored, ali ne clinical readiness decision. |
| Clinic admin | Da ako ima governance potrebu. | Ne automatski. | Moguce samo ako je eksplicitno odobreno. | Da ako je governance/admin audit potreba. | Admin pravo konfiguracije ne smije automatski davati clinical capture pravo. | Separation of duties ostaje vazan guardrail. |
| AI agent | Ne default. | Ne. | Ne. | Ne. | AI ne smije captureati, supersedeati ili finalizirati snapshot. | AI moze predlagati/analizirati samo ako buduci prompt to izricito odobri. |
| API key / integration | Ne default. | Ne default. | Ne. | Ne default. | Bilo koji write scope trazi zasebnu maintainer odluku. | Integracije ne smiju preskociti ljudski razlog i audit. |
| System job | Ne. | Ne. | Ne. | Ne. | Auto-capture u pozadini je No-Go bez zasebnog odobrenja. | Page load, nightly job ili preview read ne smiju spremiti snapshot. |

## 4. Required reason

Capture i supersession moraju traziti razlog.

Pravila:

- reason mora biti non-empty
- reason se sprema u snapshot metapodatke
- reason se sprema u audit payload
- reason je vidljiv u snapshot history UI-ju
- reason nikada ne smije biti finalno auto-generiran od AI-ja
- AI moze predloziti draft tek ako buduci governance to odobri, ali covjek ga mora potvrditi ili izmijeniti

Primjeri prihvatljivog razloga:

- "Pilot review prije kolonoskopije."
- "Ponovni capture nakon pregleda vanjskog nalaza."
- "Template version changed; spremam novi preview za usporedbu."

Neprihvatljivo:

- prazan string
- "OK"
- "AI kaze spremno"
- implicitni reason iz page loada

## 5. Permission boundary

Snapshot permission ne daje pravo na:

- clinical approval
- readiness override
- appointment status change
- task creation
- Outcome Evidence creation
- ClinicalPlan creation
- Episode update
- patient messaging
- template editing
- template binding editing
- brisanje snapshota
- editiranje snapshot payloada
- unos stvarnih pacijentovih podataka u demo/pilot nacinu

Snapshot je zapis preview prikaza u trenutku capturea.

Snapshot nije medicinska odluka sustava.

Snapshot nije dokaz ishoda.

Snapshot nije potvrda da je pacijent spreman za postupak.

## 6. B12 permission odluka

Buduca implementacija ne smije krenuti dok maintainer ne potvrdi:

- kanonska permission imena
- default role mapping
- reason requirement
- AI/API/system No-Go granice
- odnos read/write/supersede/audit_read ovlasti

Sljedeci dokument u B12 passu definira audit payload contract.
