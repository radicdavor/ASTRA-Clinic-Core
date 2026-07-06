# Program 1 - Audit Event Naming

Status: Phase A naming contract, bez migracije postojece audit povijesti

## 1. Svrha

Program 1 uvodi vise klinickih dogadjaja oko `ClinicalDocument`, AI ekstrakcije i `PatientClinicalSummary`.

Audit nazivi moraju jasno razlikovati:

- source object promjenu
- AI prijedlog
- ljudsku izmjenu
- lijecnicki pregled
- sluzbeno source-linked znanje

Ovaj dokument nije compliance odobrenje, production approval, real-data approval niti tvrdnja da je ASTRA certificirani EMR ili medicinski uredjaj.

## 2. Pravila Imenovanja

Kanonski audit event:

- koristi lowercase snake_case
- pocinje domenom ili objektom
- opisuje radnju u proslom vremenu
- ne skriva je li radnju napravio AI placeholder ili covjek
- ne koristi nejasne nazive poput `updated` kada postoji klinicki vazna semantika

AI dogadjaj i ljudska potvrda moraju ostati odvojeni.

## 3. ClinicalDocument Events

Kanonski nazivi za buduci Program 1 kod:

| Event | Znacenje |
| --- | --- |
| `clinical_document_created` | Source object je kreiran rucno ili kroz API metadata unos. |
| `clinical_document_uploaded` | Source object je nastao upload/OCR placeholder tokom. |
| `clinical_document_updated` | Metadata, raw text ili vezani source podaci su promijenjeni. |
| `clinical_document_ai_extracted` | AI/OCR placeholder je pripremio strukturirani prijedlog. |
| `clinical_document_ai_extraction_edited` | Korisnik je uredio AI strukturirani prijedlog prije pregleda. |
| `clinical_document_ai_extraction_rejected` | Odbijen je AI prijedlog/ekstrakcija; raw source ostaje dostupan. |
| `clinical_document_reviewed` | Dokument je lijecnicki pregledan i moze hraniti official source-linked knowledge. |
| `clinical_document_review_reset` | Pregled je resetiran jer se promijenio raw source ili strukturirani sadrzaj. |

## 4. PatientClinicalSummary Events

Kanonski nazivi za buduci Program 1 kod:

| Event | Znacenje |
| --- | --- |
| `patient_summary_draft_generated` | AI placeholder je generirao draft summary view iz reviewed source dokumenata. |
| `patient_summary_edited` | Korisnik je uredio summary view prije potvrde. |
| `patient_summary_reviewed` | Summary view je lijecnicki pregledan. |
| `patient_summary_review_blocked_stale` | Potvrda summary drafta je blokirana jer postoje noviji reviewed source dokumenti. |
| `patient_summary_rejected` | Buduci event ako se uvede formalno odbijanje summary recorda. |
| `patient_summary_superseded` | Buduci event ako se uvede formalno supersede lifecycle za summary record. |

Patient Clinical Summary ostaje summary view. Nije source of truth.

## 5. Compatibility Names

Postojeci kod i audit povijest mogu sadrzavati starije nazive. U Phase A ih ne treba retroaktivno migrirati ako to nije niskog rizika.

Poznati kompatibilni nazivi:

| Existing event | Canonical meaning |
| --- | --- |
| `ai_document_extracted` | `clinical_document_ai_extracted` |
| `ai_document_summary_rejected` | `clinical_document_ai_extraction_rejected` |
| `clinical_document_reviewed` | `clinical_document_reviewed` |
| `patient_summary_draft_generated` | `patient_summary_draft_generated` |
| `patient_summary_edited` | `patient_summary_edited` |
| `patient_summary_reviewed` | `patient_summary_reviewed` |

Ako se nazivi u kodu kasnije normaliziraju, potrebno je:

- zadrzati citljivost stare audit povijesti
- azurirati testove
- azurirati UI label mapiranje
- izbjeci migraciju koja mijenja smisao povijesnog dogadjaja

## 6. Granice

Ovaj dokument ne uvodi:

- real AI provider
- real OCR provider
- Clinical Readiness Gate
- Workflow Engine
- Task engine
- Episode-Based Care

Audit ovdje ostaje evidence trail za demo/pilot i razvojni hardening, a ne regulatorno odobren medicinski zapis.
