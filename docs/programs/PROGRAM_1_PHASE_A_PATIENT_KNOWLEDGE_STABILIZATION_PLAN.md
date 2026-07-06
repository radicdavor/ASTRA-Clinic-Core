# Program 1 - Phase A: Patient Knowledge Stabilization Plan

Status: implementacijski plan; Phase A1 djelomicno implementiran

## 1. Svrha

Phase A definira prvi implementation-ready planski sloj za stabilizaciju Patient Clinical Knowledge i ClinicalDocument review toka.

Ovaj dokument prevodi arhitekturu iz Program 1 dokumenata u siguran redoslijed budućih malih implementacijskih zadataka. Fokus je na tome da ASTRA jasno razlikuje izvorni dokument, AI prijedlog, pregledanu kliničku tvrdnju, sažetak i otvoreno pitanje.

Ovaj dokument nije implementacija.

Ovaj dokument nije compliance odobrenje.

Ovaj dokument nije produkcijsko odobrenje.

Ovaj dokument ne dopušta stvarne pacijentove podatke.

Ovaj dokument ne certificira ASTRA-u kao EMR.

Ovaj dokument ne certificira ASTRA-u kao medicinski uređaj.

## 2. Phase A scope

### In scope

- ClinicalDocument lifecycle hardening
- source-linked knowledge contract
- physician review workflow
- Patient Clinical Summary clarity
- open questions / unresolved findings behavior
- AI extraction placeholder boundaries
- audit evidence for review actions
- Patient Workspace display clarity
- ClinicalDocument detail display clarity
- terminology alignment with `PROGRAM_1_GLOSSARY.md`

### Out of scope

- real OCR provider
- real AI provider
- Episode-Based Care implementation
- Clinical Readiness Gate implementation
- Task engine
- Outcome Evidence object
- Medical Note formal output
- Patient Explanation formal output
- Consent lifecycle
- Procedure/Treatment templates
- real-data readiness
- production deployment
- certified EMR/medical-device claims

## 3. Current state summary

### ClinicalDocument model status

`ClinicalDocument` postoji u `backend/app/models/domain.py`.

Trenutna polja podržavaju:

- patient link
- source type
- document type
- origin/institution/author metadata
- document date
- title
- raw text
- AI summary
- key findings
- recommendations
- physician review boolean
- reviewer and review timestamp
- attachment path placeholder
- optional appointment link

Ovo je dobar foundation za source object, ali lifecycle je još izveden iz kombinacije `physician_reviewed` i prisutnosti AI polja.

### PatientClinicalSummaryRecord model status

`PatientClinicalSummaryRecord` postoji kao summary view record.

Podržava:

- summary text
- known conditions
- key findings
- open items
- risks
- recommendations
- source document IDs
- status
- generated_by
- reviewer metadata

To nije source of truth. Source of truth ostaju pregledani ClinicalDocuments i source-linked knowledge statements.

### Existing clinical document APIs

Postoje rute za:

- list/create/update clinical documents
- upload placeholder
- search
- detail
- extract
- review
- reject summary
- patient-specific documents

Rute su dovoljne za MVP foundation, ali Phase A treba pojačati status semantics i razliku između sourcea i interpreted findings.

### Existing extraction placeholder behavior

`backend/app/services/clinical_extraction.py` i postojeća route logika koriste determinističku placeholder ekstrakciju.

To nije real AI provider.

Output uključuje summary, key findings, recommendations, confidence i extraction notes, ali model trenutno ne čuva sve potencijalne lifecycle metapodatke kao zaseban status.

### Existing physician review behavior

Pregled dokumenta trenutno postavlja:

- `physician_reviewed = True`
- `reviewed_by`
- `reviewed_at`

Svaka izmjena raw texta ili extraction polja vraća dokument u nepregledano stanje.

To je dobro MVP ponašanje, ali korisnički i API status treba postati jasniji od booleana.

### Existing patient clinical summary behavior

`GET /api/patients/{patient_id}/clinical-summary` vraća structured source-linked knowledge iz reviewed documents.

Draft summary se može generirati iz reviewed documents.

Summary review postoji, ali treba dodatno pojasniti:

- summary je view
- source-linked statements su važniji od summary texta
- stale status treba biti jasnije upravljan

### Existing PatientDetail display

`PatientDetail.tsx` prikazuje:

- identity
- reviewed/awaiting document counts
- AI summary card
- source-linked knowledge cards
- internal/external documents
- procedures/pathology/lab/imaging
- appointments/invoices/audit
- knowledge sidebar

Trenutna površina dobro prati smjer, ali Phase A treba dodatno pojačati razliku između:

- source documents
- official patient knowledge
- AI draft summary
- open questions

### Existing ClinicalDocumentDetail display

`ClinicalDocumentDetail.tsx` prikazuje:

- source metadata
- original text
- AI extraction suggestion
- review/reject controls
- audit

Trenutna površina je dobra osnova, ali UI treba jasnije voditi korisnika kroz lifecycle: source -> AI suggestion -> edit/reject/review -> eligible official knowledge.

### Existing audit behavior

Audit infrastruktura postoji kroz `AuditLog` i `audit()` helper.

Trenutni događaji uključuju create/upload/update/extract/review/reject summary i patient summary review/edit.

Phase A treba standardizirati nazive događaja i osigurati da se review/reject/edited AI suggestion može rekonstruirati.

### Known limitations

- Nema real OCR providera.
- Nema real AI providera.
- `Finding` nije zaseban implemented object.
- `ClinicalDocument.physician_reviewed` je boolean, ne potpuni lifecycle.
- `PatientClinicalSummaryRecord` može biti pogrešno shvaćen kao source of truth.
- `key_findings` arrays mogu se pogrešno shvatiti kao formalni Finding object.
- Open questions nemaju vlastiti lifecycle, owner ili due date.
- Episode Engine i ClinicalPlan postoje, ali nisu dio Phase A stabilizacije.

## 4. Stabilization goals

1. Onemogućiti u UI/docs miješanje raw source documenta s interpreted findingom.
2. Onemogućiti u UI/docs miješanje Patient Clinical Summaryja sa source of truth.
3. AI extraction mora biti vidljivo draft/suggestion dok nije physician-reviewed.
4. Physician review state mora biti eksplicitan i auditabilan.
5. Source badges i source links moraju biti pouzdani i konzistentni.
6. Open questions moraju biti vidljiva operational warnings, ne automatske odluke.
7. Episode Engine ostaje deferred.
8. Clinical Readiness Gate ostaje future.
9. Demo/pilot real-data guardrails ostaju netaknuti.

## 5. Proposed implementation work packages

### A1 - ClinicalDocument Lifecycle Contract

Purpose: razjasniti ClinicalDocument statuse i lifecycle.

Plan:

- Dokumentirati trenutna polja: `raw_text`, `attachment_path`, `ai_summary`, `key_findings`, `recommendations`, `physician_reviewed`, `reviewed_by`, `reviewed_at`.
- Definirati da `ClinicalDocument` uvijek ostaje source object, ne Finding.
- Zadržati `source_type` vrijednosti: `internal`, `external`, `scanned`, `uploaded`.
- Zadržati `document_type` vrijednosti za sadašnji MVP, uz kasnije proširenje samo kroz kontrolirani vocabulary.
- Razjasniti da `raw_text` može biti OCR placeholder ili ručno unesen tekst, ne dokaz da je OCR engine implementiran.
- Razjasniti da `attachment_path` ostaje placeholder dok se ne uvede stvarno sigurno spremanje datoteka.
- Definirati da `physician_reviewed=True` znači: dokument je pregledan i njegove strukturirane stavke smiju hraniti Patient Clinical Knowledge.
- Reject behavior: odbijanje AI sažetka mora ukloniti AI structured output iz official knowledge toka.
- Audit requirements: create/upload, update source, edit extraction, review, reject, supersede.

Future implementation candidates:

- eksplicitni `review_status`
- `review_decision`
- `review_note`
- `superseded_by_document_id`

Ne stvarati migracije sada.

### A2 - AI Extraction Suggestion Lifecycle

Purpose: razjasniti AI extraction kao suggestion, ne official truth.

Plan:

- Extraction source je `ClinicalDocument.raw_text` i metadata.
- Output fields su `ai_summary`, `key_findings`, `recommendations`; confidence postoji u service outputu, ali trenutno nije trajno modeliran za document extraction.
- AI suggestion status treba biti eksplicitan u budućoj implementaciji.
- Physician review je obavezan prije official knowledge eligibility.
- Edit behavior: uređivanje AI extractiona vraća dokument u stanje koje čeka review.
- Reject behavior: odbijanje AI extractiona uklanja AI fields i ne hrani patient knowledge.
- Accept behavior: review dokumenta čini edited/extracted content eligible za Patient Clinical Knowledge.
- Audit events trebaju razlikovati generated, edited, accepted/reviewed, rejected, superseded.
- UI labeling mora koristiti `AI prijedlog`, `AI placeholder`, `čeka liječnički pregled`.

Boundary:

- Trenutna extraction logika je deterministic placeholder.
- Real AI provider nije dio Phase A.
- AI confidence nije medicinska sigurnost.

### A3 - Source-Linked Patient Knowledge Contract

Purpose: definirati što smije ući u official Patient Clinical Knowledge.

Plan:

- Samo reviewed ClinicalDocuments smiju doprinositi official Patient Clinical Knowledge.
- Svaka knowledge statement stavka mora imati barem jedan source.
- Unsourced AI statements su zabranjene kao official facts.
- Duplicate/merged statements smiju spojiti izvore ako je tekst normalizirano isti.
- Open questions moraju imati source ili jasnu oznaku da su operational warning iz reviewed sourcea.
- Source badge mora prikazati title, type/source, date/origin gdje je dostupno.
- Source link mora voditi na `/clinical-documents/{document_id}`.
- API mora nastaviti filtrirati unreviewed docs iz official knowledge outputa.

### A4 - Patient Clinical Summary Stabilization

Purpose: razjasniti Patient Clinical Summary kao summary view, ne source of truth.

Plan:

- Generated draft behavior: draft se smije generirati samo iz reviewed documents.
- Reviewed summary behavior: reviewed summary je physician-reviewed summary view.
- Stale summary behavior: summary mora biti stale ako su relevantni reviewed documents promijenjeni nakon zadnjeg reviewa.
- `source_document_ids` mora ostati traceability list, ne zamjena za per-statement sources.
- Summary UI mora prikazati status: draft, needs review, reviewed, stale.
- Draft/stale summary mora imati warning da nije službeni završni pogled.
- Physician review je potreban za reviewed summary status.
- Ako nema reviewed documents, summary ne smije glumiti clinical knowledge.

### A5 - Open Questions and Unresolved Findings

Purpose: razjasniti kako se nerazriješene informacije prikazuju i obrađuju.

Definitions:

- `Open Question`: source-linked pitanje koje treba kliničku pažnju.
- `Unresolved Finding`: reviewed finding koji još nema razriješen klinički zaključak.

Examples:

- patologija pending
- H. pylori status nepoznat
- interval nadzora nije potvrđen
- vanjski nalaz kontradiktoran
- preporuka iz vanjskog dokumenta treba reconciliaciju

Plan:

- Open questions se prikazuju u Patient Workspaceu.
- Open questions nisu automatic decisions.
- Open questions ne stvaraju task u Phase A.
- Future task conversion ostaje izvan scopea.
- Review/audit mora pokazati iz kojeg izvora je pitanje nastalo.

### A6 - Patient Workspace Clarity

Purpose: poboljšati buduće PatientDetail ponašanje.

Plan:

- Jasno odvojiti source documents section od official patient knowledge sectiona.
- Summary/draft/reviewed section mora biti označen kao summary view.
- Open questions moraju biti posebna vidljiva sekcija.
- AI suggestion labeling mora biti vidljiv na summary draftu i extraction-derived contentu.
- Source badges moraju biti dosljedne i klikabilne.
- Warning states: no reviewed documents, documents awaiting review, stale summary, draft summary.
- Ne uvoditi episode-first workflow.
- Ne prikazivati Episode Engine kao primarni klinički put.

Ne implementirati UI sada.

### A7 - ClinicalDocument Detail Clarity

Purpose: poboljšati buduće ClinicalDocumentDetail ponašanje.

Plan:

- Raw source display mora biti vidljivo odvojen od AI suggestion displaya.
- AI extraction suggestion mora imati status i warning.
- Physician review controls trebaju jasno reći što review omogućuje.
- Reject/edit/accept behavior mora biti objašnjen in-app.
- Audit/timeline mora prikazati create/upload, extraction, edit, review, reject.
- Source identity metadata mora biti u vrhu: patient, origin, institution, author, date, type.
- Attachment placeholder mora biti jasno označen kao placeholder dok nema stvarnog file storagea.

Ne implementirati UI sada.

### A8 - Audit Evidence Hardening

Purpose: definirati audit očekivanja.

Required future audit events:

- `clinical_document_created`
- `clinical_document_uploaded`
- `ai_document_extraction_generated`
- `ai_document_extraction_edited`
- `clinical_document_reviewed`
- `ai_document_extraction_rejected`
- `patient_summary_draft_generated`
- `patient_summary_reviewed`
- `patient_summary_marked_stale`
- `patient_summary_regenerated`
- `source_linked_knowledge_updated`

Audit mora moći rekonstruirati:

- tko je učinio radnju
- kada
- nad kojim dokumentom/pacijentom
- prije/poslije snapshot
- je li radnja AI suggestion ili physician review

Ne implementirati event rename sada.

### A9 - Test Strategy for Future Implementation

Purpose: definirati što buduća implementacija mora testirati.

Future tests:

- reviewed documents only contribute to official knowledge
- unreviewed AI extraction does not become official fact
- source badges exist for every knowledge statement
- stale summary detection
- reject behavior excludes AI extraction from official knowledge
- audit records for create/extract/edit/review/reject/summary review
- PatientDetail labels distinguish source, knowledge, summary and AI draft
- ClinicalDocumentDetail labels distinguish raw source, AI suggestion and reviewed content
- demo/real-data guardrails remain intact
- Episode Engine remains deferred
- Clinical Readiness Gate remains future

Ne pisati testove sada.

## 6. Proposed status models

Ovi status modeli su prijedlog za buduću implementaciju. Nisu trenutna implementacija.

### ClinicalDocument review status

Suggested statuses:

- `draft`
- `extracted`
- `needs_physician_review`
- `reviewed`
- `rejected`
- `superseded`

Current implementation:

- `review_status` postoji na `ClinicalDocument`.
- `physician_reviewed` je zadrzan kao compatibility field.
- Official Patient Clinical Knowledge zahtijeva oba uvjeta: `review_status=reviewed` i `physician_reviewed=true`.
- AI extraction ostaje deterministicki placeholder, nije stvarni AI/OCR provider.

Relationship to current `physician_reviewed: bool`:

- `physician_reviewed=True` približno odgovara `reviewed`.
- `physician_reviewed=False` ostaje kompatibilni signal za ne-pregledano stanje, ali lifecycle se cita iz `review_status`.
- Future schema change moze ukloniti compatibility boolean tek kad je sigurno za API klijente.

### AI extraction status

Suggested statuses:

- `not_run`
- `generated`
- `edited`
- `accepted`
- `rejected`
- `superseded`

Current support:

- `generated` i `edited` su implicitni kroz AI fields i audit actione.
- `accepted` je implicitno kroz document review.
- `rejected` je djelomično kroz reject-summary.
- `superseded` nije modeliran.

### Patient Clinical Summary status

Suggested statuses:

- `draft_ai`
- `needs_review`
- `reviewed`
- `stale`
- `rejected`
- `superseded`

Current support:

- `draft_ai`, `needs_review`, `reviewed`, `stale` postoje u schema validatoru.
- `rejected` i `superseded` nisu podržani.
- Future schema change može biti potreban ako se rejection/supersession uvede kao stvarni lifecycle.

## 7. Data model implications

| Current object/field | Current meaning | Phase A issue | Future implementation candidate | Migration needed? |
| --- | --- | --- | --- | --- |
| `ClinicalDocument.physician_reviewed` | Boolean review flag. | Pregrub status za lifecycle. | `review_status` field. | unknown |
| `ClinicalDocument.ai_summary` | AI placeholder summary text. | Može izgledati službeno. | `ai_extraction_status`, clearer UI labels. | unknown |
| `ClinicalDocument.key_findings` | JSON list extracted/edited items. | Može se zamijeniti s formal Finding objectom. | Keep as extracted statements or introduce Finding later. | unknown |
| `ClinicalDocument.recommendations` | JSON list extracted/edited recommendations. | Može sadržavati open questions bez lifecyclea. | Categorize recommendation/open question intent. | unknown |
| `ClinicalDocument.raw_text` | OCR/manual text placeholder. | Može se shvatiti kao real OCR result. | Add OCR metadata/status later. | unknown |
| `ClinicalDocument.attachment_path` | Placeholder path. | Nema real secure file storage semantics. | Attachment object or storage metadata later. | unknown |
| `ClinicalDocument.source_type` | internal/external/scanned/uploaded. | Dovoljno za Phase A. | Keep; extend only through glossary. | no |
| `ClinicalDocument.document_type` | consultation/gastroscopy/pathology/etc. | Dovoljno, ali procedure/treatment outputs nisu formalni. | Extend later with controlled values. | unknown |
| `ClinicalDocument.reviewed_by` | Reviewer user id. | Dobro, ali role semantics nisu detaljne. | Tie to physician/authorized clinician rules. | no/unknown |
| `ClinicalDocument.reviewed_at` | Review timestamp. | Dovoljno za Phase A. | Keep. | no |
| `PatientClinicalSummaryRecord.status` | draft/review/stale lifecycle. | Nema rejected/superseded. | Extend status set if needed. | unknown |
| `PatientClinicalSummaryRecord.source_document_ids` | Source list for summary. | Nije per-statement source. | Preserve plus per-item sources from PatientKnowledgeItem. | no |
| `PatientClinicalSummaryRecord.open_items` | Summary-level unresolved items. | Nema source per item u recordu. | Keep summary view; official open questions from PatientKnowledgeItem. | unknown |
| `PatientClinicalSummaryRecord.known_conditions` | Summary list. | Može zvučati kao diagnosis registry. | Label as summary view. | no |
| `PatientClinicalSummaryRecord.key_findings` | Summary list. | Može se zamijeniti s Finding objectom. | Label as summary view. | no |
| `PatientClinicalSummaryRecord.reviewed_by` | Summary reviewer. | Dobro, ali physician semantics treba pojasniti. | Keep and validate role later. | no/unknown |
| `PatientClinicalSummaryRecord.reviewed_at` | Summary review time. | Dovoljno za traceability. | Keep. | no |

## 8. API implications

| Current route/area | Current behavior | Phase A concern | Future implementation candidate |
| --- | --- | --- | --- |
| clinical document create/list/detail | CRUD/list/detail za ClinicalDocument. | Status nije pun lifecycle. | Add/derive clear review lifecycle response. |
| clinical document extract | Generira placeholder AI fields. | Može se tretirati kao real AI ili official fact. | Explicit AI suggestion status and labels. |
| clinical document review | Postavlja physician_reviewed. | Boolean skriva razliku accept/edit/review. | Review decision metadata/status. |
| clinical document reject | Briše AI summary/findings/recommendations i resetira review. | Rejection status nije trajan kao lifecycle. | Explicit rejected/superseded state if needed. |
| patient clinical summary generation | Draft iz reviewed documents. | Draft može izgledati kao official summary. | Stronger response labels and stale metadata. |
| patient clinical summary review | Potvrđuje summary record. | Summary review može se zamijeniti s source truth. | Clarify in API docs/output naming. |
| patient clinical summary display | Vraća source-linked categories i summary records. | Potrebno zadržati source links za official items. | Contract tests for source links. |
| patient workspace data loading | PatientDetail učitava patient, docs, summary, appointments, invoices, audit. | UI može biti pretrpan i summary-first. | Clarify sections and warning states. |
| readiness checks for unreviewed documents/stale summaries | Operational readiness warning. | Ne smije postati Clinical Readiness Gate. | Keep Operational Readiness naming. |

Ne dizajnirati finalne endpoint specifikacije u ovom planskom dokumentu.

## 9. Frontend implications

| Current page/component | Current behavior | Phase A concern | Future implementation candidate |
| --- | --- | --- | --- |
| `PatientDetail` | Prikazuje AI summary, knowledge cards, docs, open questions. | Summary i official knowledge mogu se vizualno miješati. | Jasnije zone: source docs, official knowledge, summary view, open questions. |
| `ClinicalDocuments` | Upload/list/filter docs. | Upload/OCR placeholder treba biti jasnije označen. | Stronger helper text/status labels. |
| `ClinicalDocumentDetail` | Raw text, AI extraction, review/reject, audit. | AI suggestion i reviewed content trebaju lifecycle clarity. | Explicit lifecycle header/status panel. |
| source badges | Linkaju na source docs. | Moraju biti prisutni za svaku official statement. | Smoke test/source badge contract. |
| summary cards | Prikazuju AI/reviewed summary. | Summary nije source of truth. | Copy and layout that says "summary view". |
| open questions display | Sidebar/cards. | Može djelovati kao odluka. | Label as operational warnings requiring review. |
| stale/draft/reviewed labels | Postoje djelomično. | Stale/draft warning treba biti snažniji. | Status-specific banner. |
| review/reject buttons | Postoje u document detailu. | Accept/reject semantics nisu potpuno vidljive. | Clarify button help and confirmation copy. |
| warning/help text | Postoji kroz HelpHint. | Treba dosljedno koristiti glossary. | Copy pass in Phase A UI task. |

Ne implementirati UI sada.

## 10. Acceptance criteria for future Phase A implementation

1. Unreviewed AI extraction cannot appear as official clinical fact.
2. Patient Clinical Summary is visibly draft/reviewed/stale.
3. Every official knowledge statement has a source link.
4. ClinicalDocument review status is clearer than a hidden boolean.
5. Rejected AI extraction/document summary does not feed official knowledge.
6. Open questions are visible but not treated as decisions.
7. Patient Workspace distinguishes source documents, official knowledge and summary.
8. ClinicalDocumentDetail distinguishes raw source, AI suggestion and reviewed content.
9. Audit captures review and rejection events.
10. Existing demo/pilot guardrails remain intact.
11. Episode Engine remains deferred.
12. Clinical Readiness Gate remains future.
13. Backend tests cover knowledge inclusion/exclusion rules.
14. Frontend tests or smoke checks cover labels and source links.
15. No real patient data is introduced.

## 11. Safe future Codex task sequence

| Task | Purpose | Files likely touched | Risks | Tests likely needed |
| --- | --- | --- | --- | --- |
| Phase A1 documentation-to-code alignment check | Confirm current behavior before code changes. | Docs, maybe no code. | Starting implementation without exact baseline. | No tests if docs-only. |
| ClinicalDocument review status hardening | Make review lifecycle explicit. | `domain.py`, `common.py`, `core.py`, migration, FE types/pages. | Overbuilding status model. | Backend lifecycle tests; FE status smoke. |
| AI extraction lifecycle hardening | Separate generated/edited/accepted/rejected. | `clinical_extraction.py`, `core.py`, FE detail page. | AI placeholder looks like real AI. | Extraction/reject/review tests. |
| Patient Clinical Summary stale/draft/reviewed clarity | Strengthen summary status behavior. | `core.py`, schemas, `PatientDetail.tsx`. | Summary becomes source of truth. | Stale detection tests; UI label checks. |
| Source-linked knowledge contract tests | Enforce official knowledge source links. | Backend tests, possibly summary builder. | Unsourced facts leak into UI. | Contract tests for every item sources. |
| Patient Workspace clarity UI pass | Separate zones and warning states. | `PatientDetail.tsx`, CSS/components. | UI becomes form-heavy. | Smoke/visual label checks. |
| ClinicalDocumentDetail clarity UI pass | Make source/suggestion/review lifecycle obvious. | `ClinicalDocumentDetail.tsx`, maybe components. | Users confirm without understanding. | Smoke checks for labels/actions. |
| Audit event hardening | Standardize audit names and snapshots. | `core.py`, audit tests. | Breaking existing audit expectations. | Audit event tests. |
| Phase A regression/smoke validation | Verify no pilot flow broke. | Tests only. | Hidden regression in appointments/readiness. | Backend + frontend smoke/build as appropriate. |
| Phase A documentation update | Record implemented behavior. | Docs. | Docs drift from code. | No tests if docs-only. |

## 12. Risks and non-goals

### Risks

- Overbuilding Workflow Engine too early.
- Making ClinicalEpisode primary too early.
- Treating AI placeholder as real AI.
- Hiding source transparency behind summary text.
- Making UI too form-heavy.
- Confusing Patient Clinical Summary with truth.
- Creating too many status fields too early.
- Breaking demo seed/pilot behavior.
- Creating a separate Finding object before lifecycle proves it is necessary.
- Mixing Operational Readiness with future Clinical Readiness Gate.

### Non-goals

- No Episode-Based Care implementation.
- No Clinical Readiness Gate implementation.
- No Task engine.
- No Outcome Evidence object.
- No Medical Note formal output.
- No Patient Explanation formal output.
- No Consent lifecycle.
- No real OCR.
- No real AI provider.
- No production or certification claim.

## 13. Go / No-Go recommendation

Recommendation: Go with narrow implementation tasks.

Recommended first actual implementation task:

`Program 1 Phase A1 - ClinicalDocument Review Status Hardening`

Reason:

- `ClinicalDocument` is already the source object foundation.
- Current `physician_reviewed` boolean hides multiple lifecycle states.
- Patient Clinical Knowledge depends on reviewed documents.
- This can be implemented narrowly without reactivating Episode-Based Care, Clinical Readiness Gate, Task engine or Workflow Engine.

The first implementation task should be small, testable and limited to ClinicalDocument review lifecycle semantics, labels, audit and source-linked knowledge safety.
