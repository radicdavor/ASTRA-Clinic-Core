# Program 1 - Domain Object Mapping

Status: arhitektonsko mapiranje pojmova na postojeću implementaciju, bez implementacije

## 1. Svrha

Ovaj dokument mapira kanonski rječnik iz `PROGRAM_1_GLOSSARY.md` na postojeću implementaciju ASTRA Clinic Core repozitorija.

Svrha je jasno pokazati što već postoji, što je djelomično implementirano, što je samo dokumentacijski koncept, što je deferred i što je buduća praznina za implementaciju.

Ovaj dokument nije implementacija.

Ovaj dokument nije compliance odobrenje.

Ovaj dokument nije produkcijsko odobrenje.

Ovaj dokument ne dopušta stvarne pacijentove podatke.

Ovaj dokument ne certificira ASTRA-u kao EMR.

Ovaj dokument ne certificira ASTRA-u kao medicinski uređaj.

## 2. Mapping principles

- Čuvati kanonski rječnik iz `PROGRAM_1_GLOSSARY.md`.
- Razlikovati current implemented objects od future concepts.
- Ne tumačiti postojeći kod kao zreliji nego što jest.
- Ne tretirati deferred Episode Engine kao primarni workflow.
- Ne tretirati AI placeholder logiku kao stvarni AI provider.
- Ne tretirati readiness cockpit kao Clinical Readiness Gate.
- Source-linked Patient Clinical Knowledge ostaje primarni klinički temelj.
- Svaka buduća implementation gap stavka mora biti eksplicitna.

## 3. Current implementation overview

Backend koristi Python FastAPI, SQLAlchemy 2.x, PostgreSQL i Alembic migracije.

Frontend koristi React, TypeScript i Vite.

Trenutni primarni domain modeli nalaze se u `backend/app/models/domain.py` i uključuju pacijente, termine, usluge, providere, sobe, module, audit, API ključeve, inventar, nabavu, račune, kliničke dokumente, patient clinical summary records, kliničke epizode i kliničke planove.

Trenutne API površine uključuju:

- patient APIs
- appointment APIs
- reception/day APIs
- clinical document APIs
- patient clinical summary APIs
- episode APIs
- clinical plan APIs
- readiness API
- inventory/material APIs
- invoice APIs
- AI agent APIs
- auth/API key APIs
- audit APIs

Trenutne workspace površine uključuju:

- Patient Workspace preko `frontend/src/pages/PatientDetail.tsx`
- Appointment Workspace preko `frontend/src/pages/AppointmentDetail.tsx`
- Reception Workspace preko `frontend/src/pages/Reception.tsx`
- Episode Workspace preko `frontend/src/pages/EpisodeDetail.tsx`, ali kao deferred/compatibility površinu
- ClinicalDocument review površinu preko `ClinicalDocuments.tsx` i `ClinicalDocumentDetail.tsx`
- Readiness površinu preko `Readiness.tsx`
- Inventory i Invoices površine

Patient knowledge support postoji kroz `ClinicalDocument`, `PatientClinicalSummaryRecord`, source badges, clinical summary endpoint i Patient Workspace prikaz.

Clinical document support postoji kao registry, upload metadata/raw text placeholder, AI extraction placeholder, physician review i reject summary tok.

Readiness support postoji kao Operational Readiness cockpit preko `/api/readiness` i `/readiness`.

Inventory/billing support postoji kao operativni sloj za artikle, batch/lot, stock movements, purchase orders, invoices, payments i material consumption.

AI support je placeholder:

- `clinical_extraction.py` i inline extraction/propose logic koriste deterministička pravila
- nema stvarnog AI providera
- AI output mora ostati draft/suggestion dok ga čovjek ne pregleda ili potvrdi

## 4. Canonical term to implementation mapping

| Canonical term | Current implementation object/file | Current status | Notes | Future gap |
| --- | --- | --- | --- | --- |
| `Patient` | `Patient` model, `PatientCreate/Out`, `/api/patients`, `PatientDetail.tsx` | Implemented | Osnovni objekt sustava. | Daljnje jačanje identiteta i duplicate resolution. |
| `Patient Workspace` | `PatientDetail.tsx`, workspace components | Implemented | Primarna klinička površina; prikazuje knowledge, dokumente, termine, račune, audit. | Dodatno očistiti terminology oko summary vs source of truth. |
| `Appointment` | `Appointment` model, appointment schemas/routes/pages | Implemented | Operativni time/resource object. | Clinical readiness status nije dio termina. |
| `Appointment Workspace` | `AppointmentDetail.tsx` | Partially implemented | Prikazuje termin, epizodu, materijale, račun, audit. | Clinical Readiness Gate nije implementiran. |
| `Reception Workspace` | `/api/reception/day`, `Reception.tsx` | Implemented | Arrival, identity verification, resource scheduling. | Week/month view deferred; nije klinička istina. |
| `Service` | `Service` model, `/api/services`, `Services.tsx` | Implemented | Katalog usluga s duration/price/module. | Specialty procedure semantics nisu formalizirane. |
| `Provider` | `Provider` model, `/api/providers` | Implemented | Provider/staff role i clinic link postoje. | Granice physician vs nurse/admin confirmation treba formalizirati. |
| `Room` | `Room` model, `/api/rooms`, room-services relation | Implemented | Resurs rasporeda. | Napredna resource capability pravila nisu dio Program 1. |
| `ClinicalDocument` | `ClinicalDocument` model/schemas/routes/pages | Implemented | Source object za patient knowledge; `review_status` eksplicitno prati draft/needs review/reviewed/rejected lifecycle, a `physician_reviewed` ostaje compatibility field. `reject-summary` odbija AI ekstrakciju, ne raw source. | Attachment/OCR su placeholderi; supersede workflow nije implementiran. |
| `Finding` | `key_findings` JSON na `ClinicalDocument` i summary itemi | Partially implemented | Nije zaseban object; može se zamijeniti s raw documentom. | Odlučiti ostaje li derived output ili postaje objekt. |
| `Internal ClinicalDocument` | `source_type=internal` | Implemented | Podržano u schema validaciji i UI labelama. | Interni Medical Note/Procedure Report nisu formalni outputi. |
| `External ClinicalDocument` | `source_type=external/scanned/uploaded` | Implemented | Vanjski dokumenti su first-class source inputs. | File storage/OCR nisu stvarni provider. |
| `Patient Clinical Knowledge` | `/patients/{id}/clinical-summary`, `PatientKnowledgeItem`, PatientDetail cards, `patient_knowledge.py` helpers, Phase A regression gate tests | Partially implemented | Source-linked summary categories postoje; A8 regression gate stiti official knowledge invariants. | Treba formalnije odvojiti official facts od future Finding objecta. |
| `Patient Clinical Summary` | `PatientClinicalSummaryRecord`, summary endpoints, PatientDetail AI/reviewed summary card | Implemented | Summary record/status i stale detection postoje; UI labelira summary kao pomocni view. | Ne smije se tretirati kao source of truth. |
| `Open Question` | `open_questions`, `open_items`, `PatientKnowledgeItem.display_kind/severity/requires_attention` | Implemented foundation | Prikazuje pregledane, source-linked nerazrijesene stavke kao warning/question, odvojeno od preporuka i summary viewa. | Nema lifecycle, owner, due date ili task conversion. |
| `Unresolved Finding` | `open_items`, recommendations pending text, reviewed source-linked open questions | Partially implemented | Izvedeno iz reviewed documents/placeholder extraction. Nije zaseban objekt. | Nema formalni status model. |
| `Source-Linked Statement` | `PatientKnowledgeItem.sources`, `SourceBadge` | Implemented | Svaka prikazana knowledge stavka ima sources. | Enforce pravila treba čuvati u budućim endpointima. |
| `Physician Review` | `ClinicalDocument.physician_reviewed`, review endpoints, summary review endpoint | Implemented | Review postoji za docs i summary. | Treba razjasniti physician-only vs authorized human. |
| `Clinical Workflow` | Program 1 docs | Documentation-only | Nije runtime workflow engine. | Planiranje implementacije po fazama. |
| `Patient Journey` | `PROGRAM_1_PATIENT_JOURNEY_MODEL.md` | Documentation-only | Idealni klinički put. | Nema zasebni runtime model. |
| `Clinical Episode` | `ClinicalEpisode` model/routes/pages | Partially implemented / Deferred | Objekt postoji, ali nije primary workflow. | Reaktivirati tek nakon knowledge stabilization. |
| `Episode-Based Care` | Program 1 episode model docs | Deferred | Budući organizacijski model. | Ne uvoditi prije patient knowledge stabilnosti. |
| `ClinicalPlan` | `ClinicalPlan` model/routes, EpisodeDetail UI | Partially implemented / Deferred | AI suggestion/confirm tok postoji u epizodi. | Nije workflow engine i nije patient-level plan. |
| `Task` | Nema generički Task model | Not represented | Task je dokumentacijski pojam. | Odlučiti generički operational task vs clinical-only. |
| `Follow-up` | Appointment statuses, ClinicalPlan next_action/suggested_follow_up | Partially implemented | Pojavljuje se kao status/tekst. | Nema formalni follow-up object. |
| `Outcome Evidence` | Audit/logs i neki statuses | Future concept | Nema zaseban evidence contract. | Definirati minimalni outcome record. |
| `Episode Closure` | `/episodes/{id}/close`, episode status/end_date | Partially implemented / Deferred | Close endpoint postoji, ali nije puni closure model. | Closure reason/evidence/communication nisu formalizirani. |
| `Surveillance` | Documentation/status examples | Future concept | Nije aktualni status u EPISODE_STATUSES. | Dodati tek uz episode reactivation. |
| `Referral` | ClinicalDocument document_type=`referral` | Partially implemented | Kao dokument tip postoji. | Referral kao workflow outcome nije implementiran. |
| `Lost to Follow-up` | Documentation-only | Future concept | Nema runtime status. | Definirati kasnije u outcome/episode modelu. |
| `Administrative Closure` | Documentation-only | Future concept | Nema closure reason model. | Definirati uz Episode Closure. |
| `Operational Readiness` | `/api/readiness`, `Readiness.tsx`, docs | Implemented | Demo/pilot readiness cockpit. | Ne miješati s Clinical Readiness Gateom. |
| `ASTRA Readiness Model` | `ASTRA_READINESS_MODEL.md`, readiness route | Implemented | Read-only operational risk view. | Ostaje non-compliance. |
| `Clinical Readiness Gate` | Program 1 Phase B0/B1/B2 docs plus B3/B4/B5/B6/B7 preview | Implemented read-only preview only | B3 dodaje appointment-scoped, non-blocking preview endpoint i Appointment Workspace prikaz. B4 dodaje staticne demo/pilot template definicije i service-name matching. B5 dodaje template selection metadata i binding transparency. B6 dodaje demo explicit service binding prije keyword fallbacka. B7 dodaje demo template version metadata. Nema enforcement, override, task, DB model ili persistent gate. | Sljedeci korak je Clinical Readiness Snapshot Design. |
| `Clinical Readiness Snapshot` | `ClinicalReadinessSnapshot`, `clinical_readiness_snapshots`, migration `0014_clinical_readiness_snapshots.py` | Persistence foundation only | B13 dodaje DB shape za immutable copied preview payload, reason, disclaimer, template metadata i future supersession fields. Nema capture servicea, endpointa, UI-ja, audit writea ili permission enforcementa. | Snapshot Capture Service Prototype prije javnog endpointa ili UI capture buttona. |
| `Ready` | Documentation-only readiness status for future gate | Future concept | Nije runtime clinical status. | Koristiti kao `clinical_readiness_status`. |
| `Ready with Warning` | Documentation-only | Future concept | Nije runtime clinical status. | Treba override/audit semantics. |
| `Not Ready` | Documentation-only | Future concept | Nije runtime clinical status. | Treba reason i next action. |
| `Needs Physician Review` | Document review/readiness warning concepts | Partially implemented | Postoji kroz unreviewed docs, ali nije clinical gate status. | Ne koristiti bez qualifiera. |
| `Needs Nurse Action` | Documentation-only | Future concept | Nema runtime object. | Definirati uz task model. |
| `Needs Missing Document` | Readiness warning and docs concepts | Partially implemented | Nepregledani documents postoje; missing specific source ne. | Potreban missing source model. |
| `Needs Consent` | Documentation-only | Future concept | Consent nije formaliziran. | Consent lifecycle kasnije. |
| `Needs Rescheduling` | Appointment status `rescheduled` | Partially implemented | Status termina postoji, ali nije clinical readiness outcome. | Razdvojiti scheduling status od gate statusa. |
| `AI Suggestion` | ClinicalDocument extraction, ClinicalPlan generation, UI labels | Partially implemented | ClinicalDocument AI extraction lifecycle je eksplicitan; output ostaje prijedlog dok dokument nije pregledan. | Siru cross-domain AI suggestion taksonomiju jos treba uskladiti kasnije. |
| `AI Draft` | PatientClinicalSummaryRecord `draft_ai`, summary card | Partially implemented | Draft status postoji. | Razdvojiti draft types po domainu. |
| `AI Extraction` | `/clinical-documents/{id}/extract`, `extract_document_knowledge`, `ClinicalDocument.ai_extraction_status` | Partially implemented | Deterministički placeholder, nije real AI; lifecycle razlikuje `not_run`, `generated`, `edited`, `accepted`, `rejected`, `superseded`. | Integracija real AI providera nije dio sadašnjeg scopea; supersede workflow nije implementiran. |
| `AI Confidence` | `ClinicalPlan.ai_confidence` | Partially implemented | Postoji za plan suggestion. | Nije za document extraction. |
| `Physician Confirmation` | `confirm_clinical_plan`, summary/document review | Partially implemented | Potvrde postoje u više tokova. | Potrebna jedinstvena semantika confirmationa. |
| `Human Confirmation` | Recepcija/identity/payment actions | Partially implemented | Operativne potvrde postoje, ali nisu nazvane ovim pojmom. | Granice s physician confirmation. |
| `Accepted AI Suggestion` | confirmed ClinicalPlan, reviewed summary/document | Partially implemented | Postoji ponašanje, ne jedinstven lifecycle object. | Status mapping. |
| `Rejected AI Suggestion` | `/clinical-plans/{id}/reject`, `/clinical-documents/{id}/reject-summary` | Partially implemented | Odbijanje postoji u dva domaina. | Uskladiti naming/audit events. |
| `Deferred AI Suggestion` | pending ClinicalPlan, unreviewed extracted document | Partially implemented | Postoji kao pending state. | Formalni status nije univerzalan. |
| `Superseded AI Suggestion` | Nema univerzalno | Not represented | Povijest zamjene nije modelirana. | Dodati samo ako audit zahtijeva. |
| `Medical Note` | Documentation-only; raw_text/ClinicalDocument može sadržati note | Future concept | Nema formalni output. | Definirati nakon document hardeninga. |
| `Patient Explanation` | Program docs only | Future concept | Nema formalni output/document. | Treba physician/human confirmation. |
| `Consent` | Documentation-only | Future concept | Nema model/status. | Consent lifecycle i source storage. |
| `Procedure Report` | ClinicalDocument document_type gastroscopy/colonoscopy | Partially implemented | Report može biti dokument, ali nije formalni output. | Definirati procedure output. |
| `Treatment Record` | Documentation-only | Future concept | Nema formalni estetski treatment record. | Kasnije procedure/treatment templates. |
| `Audit Evidence` | `AuditLog`, `audit()` service, `AuditTimeline`, Clinical Evidence Timeline | Implemented | Tehnicka audit infrastruktura postoji; A7 dodaje citljiv, read-only timeline preko postojecih ClinicalDocument audit dogadjaja. | Bogatija patient-wide clinical event semantika ostaje future. |
| `Clinical Evidence Loop` | Program docs | Documentation-only | Nije zasebni runtime layer. | Hardening nakon outcome evidence. |
| `Operational Evidence Loop` | Readiness/audit/docs | Implemented concept | Operativni loop postoji. | Pilot docs ostaju decision source. |
| `Source Object` | `ClinicalDocument`, future procedure/treatment reports | Partially implemented | ClinicalDocument je glavni source object. | Formalizirati druge source objecte. |
| `Official Clinical Fact` | Reviewed docs/summary-derived items | Partially implemented | Koncept postoji kroz reviewed sources. | Nema zaseban model. |
| `Procedure` | Service/document_type examples | Partially implemented | Postupci postoje kao usluge/dokumenti. | Nema formalni Procedure object/report lifecycle. |
| `Treatment` | Service/catalog/docs | Future concept | Nije formalno odvojen od procedure/service. | Tretman template kasnije. |
| `Material Consumption` | service material templates, consume endpoints, stock movements | Implemented | Operativno vezano uz appointment. | Clinical treatment semantics nisu potpuno povezane. |
| `Product` | `InventoryItem` | Implemented | Artikli/proizvodi u inventaru. | Klinički product use semantics kasnije. |
| `Batch/Lot` | `InventoryBatch.lot_number` | Implemented | Lot tracking postoji. | Treatment record linkage kasnije. |
| `Inventory Movement` | `StockMovement` | Implemented | Kretanja su auditabilna. | Klinički outcome nije iz toga automatski izveden. |

## 5. Backend domain model mapping

| Existing model | Canonical Program 1 term | Current role | Alignment | Future changes needed |
| --- | --- | --- | --- | --- |
| `Patient` | `Patient` | Osoba i centralni objekt. | Aligned | Jačanje identity/duplicate guardrails. |
| `Appointment` | `Appointment` | Time/resource object s patient/service/provider/room/status. | Aligned | Dodati Clinical Readiness Gate kasnije bez pretvaranja termina u epizodu. |
| `ClinicalEpisode` | `Clinical Episode` | Implementirani epizodni objekt. | Partially aligned / deferred | Ostaje compatibility/deferred; ne primary workflow. |
| `ClinicalPlan` | `ClinicalPlan` | Episode-bound plan suggestion/confirmation model. | Partially aligned | Ne tretirati kao full workflow engine; razmotriti patient-level context kasnije. |
| `ClinicalDocument` | `ClinicalDocument`, `Source Object` | Source object za patient knowledge. | Aligned | `review_status` hardening postoji; OCR/file storage i supersede workflow ostaju future. |
| `PatientClinicalSummaryRecord` | `Patient Clinical Summary` | Summary view/draft/review record with validated statuses and dynamic stale detection. | Aligned with caution | Summary nije source of truth; rejected/superseded summaries ostaju non-current view records. |
| `Service` | `Service` | Katalog usluga. | Aligned | Procedure/treatment semantics tek kasnije. |
| `Provider` | `Provider` | Pružatelj usluge i potencijalni physician owner. | Aligned | Confirmation role granice. |
| `Room` | `Room` | Fizički resource. | Aligned | Capability rules ostaju future. |
| `InventoryItem` | `Product` | Artikli/proizvodi. | Partially aligned | Razlikovati clinical product use od stock itema. |
| `InventoryBatch` | `Batch/Lot` | Serija, rok i količina. | Aligned | Jača veza s treatment/procedure record kasnije. |
| `StockMovement` | `Inventory Movement`, `Material Consumption` | Auditabilna promjena zalihe. | Aligned | Clinical semantics iznad movementa kasnije. |
| `Invoice` | Billing object | Financijski prikaz usluge. | Outside Program 1 core but aligned | Ne uvoditi fiscalization claims. |
| `AuditLog` | `Audit Evidence` | Audit infrastruktura. | Aligned | Rich clinical event taxonomy. |
| `ApiKey` | AI/API integration control | Scoped external/agent access. | Aligned | Minimal permissions for future AI agents. |
| `Module` | Modular architecture | Modul registry. | Aligned | Specialty protocols kasnije kroz shared vocabulary. |

## 6. Schema and API route mapping

| Area | Existing file/route | Canonical terms represented | Current limitation | Future Program 1 implication |
| --- | --- | --- | --- | --- |
| Patient APIs | `patients.py`, `/api/patients`, `/api/patients/{id}` | `Patient` | Identity guardrails su osnovni. | Patient remains first anchor. |
| Appointment APIs | `appointments.py`, `/api/appointments`, `/api/schedule/day` | `Appointment`, `Appointment Workspace` | Nema clinical readiness status. | Dodati gate kasnije kao zaseban kontekst. |
| Reception/day APIs | `reception.py`, `/api/reception/day`, `/appointments/{id}/mark-arrived` | `Reception Workspace`, `Human Confirmation` | Arrival/identity, ne clinical truth. | Zadrzati operativni scope. |
| Clinical document APIs | `clinical_documents.py`, `/api/clinical-documents*` | `ClinicalDocument`, `AI Extraction`, `Physician Review`, Clinical Evidence Timeline | OCR/AI su placeholder; finding nije zaseban object; evidence timeline je read-only view preko audit loga. | Patient-wide evidence timeline ostaje future. |
| Patient clinical summary APIs | `patient_clinical_summary.py`, `/patients/{id}/clinical-summary*` | `Patient Clinical Summary`, `Patient Clinical Knowledge` | Summary moze biti pogresno shvacen kao source of truth. | Jasnije API/docs semantics. |
| Search API | `search.py`, `/api/search` | Operational lookup | Search nije clinical reasoning. | Buduci semantic/AI search zahtijeva posebnu odluku. |
| Catalog APIs | `catalog.py`, `/api/services`, `/api/clinics`, `/api/modules`, `/api/providers`, `/api/rooms` | `Service`, `Provider`, `Room`, `Module`, clinic configuration | Operativni katalog, ne clinical workflow. | Procedure/treatment semantics tek kasnije. |
| Episode APIs | `episodes.py`, `/api/episodes*` | `Clinical Episode`, `Episode Closure` | Deferred as primary workflow. | Ne siriti prije knowledge stabilization. |
| Clinical plan APIs | `episodes.py`, `/episodes/{id}/clinical-plans*`, `/clinical-plans/{id}*` | `ClinicalPlan`, `AI Suggestion`, `Physician Confirmation` | Episode-bound i nije full workflow engine. | Lifecycle/naming mapping prije prosirenja. |
| Readiness API | `readiness.py`, `/api/readiness` | `Operational Readiness`, `ASTRA Readiness Model` | Ime `readiness` moze zbuniti s Clinical Readiness Gateom. | Buduci clinical readiness mora imati kvalificirano ime. |
| Inventory/material APIs | `inventory.py`, `/inventory/*`, `/services/{id}/materials`, `/appointments/{id}/consume-materials` | `Product`, `Batch/Lot`, `Inventory Movement`, `Material Consumption` | Operativno, ne formalno clinical treatment semantics. | Linkati s Procedure/Treatment tek kasnije. |
| Invoice APIs | `/invoices*`, `/appointments/{id}/draft-invoice` | Billing object, audit | Fiscalization je noop/stub. | Ne koristiti kao real fiscalization. |
| AI agent APIs | `ai.py`, `/api/ai/*` | AI/API agent access | Kreira pacijenta/termin i free slots; nije clinical AI. | Scope mora ostati minimalan. |
| Auth/API key APIs | `auth.py`, `/auth/login`, `/auth/api-keys` | RBAC/API key control | Nije clinical governance samo po sebi. | Future AI agents need least privilege. |
| Audit APIs | `audit.py`, `/api/audit-log` | `Audit Evidence` | Genericki entity/action log. | Dodati richer clinical event names kasnije. |

## 7. Frontend surface mapping

| Frontend page/component | Current purpose | Canonical terms represented | Alignment | Future gap |
| --- | --- | --- | --- | --- |
| `PatientDetail` | Patient Workspace s knowledge summary, documents, appointments, invoices, audit. | `Patient Workspace`, `Patient Clinical Knowledge`, `Patient Clinical Summary` | Aligned | Bolje razdvojiti official knowledge od AI summary carda. |
| `ClinicalDocuments` | Popis/filter/upload clinical documents. | `ClinicalDocument`, `Internal/External ClinicalDocument` | Aligned | Upload je metadata/raw text placeholder. |
| `ClinicalDocumentDetail` | Review workspace za document, extraction, lijecnicki pregled, audit i evidence timeline. | `ClinicalDocument`, `AI Extraction`, `Physician Review`, `Audit Evidence` | Aligned | Phase A7 dodaje read-only evidence timeline; Finding lifecycle nije formaliziran. |
| `EpisodeDetail` | Episode workspace s active/pending planovima. | `Clinical Episode`, `ClinicalPlan`, `AI Suggestion` | Partially aligned / deferred | Ostaje compatibility surface do reactivationa. |
| `AppointmentDetail` | Appointment workspace, materials, invoice, audit, read-only clinical readiness preview with template, binding, version and snapshot non-implementation metadata. | `Appointment`, `Material Consumption`, `Inventory Movement`, `Clinical Readiness Preview` | Aligned with caution | Preview nije enforcement i ne smije postati task/override/template editor/snapshot capture surface bez zasebnog governance contracta. |
| `Reception` | Day resource grid, arrival, identity verification. | `Reception Workspace`, `Human Confirmation` | Aligned | Week/month view deferred; no clinical truth. |
| `Readiness` | Operational readiness cockpit. | `Operational Readiness`, `ASTRA Readiness Model` | Aligned | UI title "Spremnost" needs future qualifier if clinical readiness appears. |
| `Inventory` | Stock overview. | `Product`, `Inventory Movement` indirectly | Partially aligned | Nema Inventory Item Workspace. |
| `Invoices` | Billing/payment/fiscalization status. | Billing support, audit | Aligned outside Program 1 | Fiscalization remains noop/stub. |
| Shared workspace components | Header/layout/sections/tabs. | Workspace architecture | Aligned | Future object workspaces should reuse. |
| API client/types | REST client, mutation toast, TypeScript DTOs. | API schemas and user feedback | Partially aligned | Toast names use "Klinicki plan" and "AI prijedlog"; okay but future naming should follow glossary. |

## 8. Program 1 implementation gaps

| Gap | Related canonical terms | Current state | Risk if implemented too early | Recommended future phase |
| --- | --- | --- | --- | --- |
| Clinical Readiness Gate not fully implemented | `Clinical Readiness Gate`, `Clinical Readiness Status`, `Clinical Readiness Item` | B3 read-only preview plus B4 static demo/pilot templates, B5 metadata transparency, B6 demo explicit binding, B7 demo version metadata, B8 snapshot non-implementation metadata, B9 snapshot persistence design docs, B10 migration review, B11 capture endpoint design, B12 permission/audit contracts and B13 persistence table/model | Confusion with `/api/readiness`; false clinical safety signal; premature blockers without override governance; static keyword/name/code config, demo version metadata and snapshot metadata could be mistaken for production rules; future capture could be mistaken for clinical approval if permission/audit/reason rules are not implemented. | Snapshot Capture Service Prototype before endpoint, UI capture button, editor or enforcement |
| Task object not implemented | `Task`, `Follow-up` | Not represented | Workarounds in notes/status fields. | Task and Follow-up Foundation |
| Finding not a separate implemented object | `Finding`, `Source-Linked Statement` | JSON arrays/summary items | Duplicate facts or confusing source vs interpretation. | ClinicalDocument Review Hardening |
| Outcome Evidence not implemented | `Outcome Evidence` | Documentation-only | Closure without evidence. | Outcome Evidence Foundation |
| Episode Closure not formalized | `Episode Closure` | Simple close endpoint/status | Premature closure of clinical story. | Episode-Based Care Reactivation |
| Patient Explanation not formalized | `Patient Explanation` | Documentation-only | Patient-facing text could be treated as generic summary. | Medical Note and Patient Explanation Outputs |
| Medical Note not formalized | `Medical Note` | Documentation-only/raw document possible | Professional output lacks review/finalization lifecycle. | Medical Note and Patient Explanation Outputs |
| Consent lifecycle not formalized | `Consent`, `Needs Consent` | Documentation-only | Clinical readiness may proceed without documented consent semantics. | Clinical Readiness Gate Prototype |
| AI suggestion lifecycle not fully implemented | `AI Suggestion`, `Accepted/Rejected/Deferred/Superseded AI Suggestion` | Multiple local statuses | Inconsistent review behavior. | AI Suggestion Lifecycle |
| Official Clinical Fact not formalized | `Official Clinical Fact` | Derived from reviewed docs/summaries | Summary could be mistaken as truth. | Patient Clinical Summary Alignment |
| Clinical Evidence Loop not implemented as distinct layer | `Clinical Evidence Loop`, `Outcome Evidence` | Documentation-only | Actions/audit not tied to outcomes. | Clinical Evidence Loop Hardening |
| Core route file remains oversized | Program 1 API surfaces | A9 je premjestio ClinicalDocument helper logiku i Operational Readiness builder u servisni sloj, ali `core.py` i dalje sadrzi vise route domena. | Buduci rad moze slucajno mijesati semantike ako se route granice ne planiraju. | Core Route Domain Split Plan |
| Specialty procedure/treatment templates not implemented | `Procedure`, `Treatment`, `Procedure Report`, `Treatment Record` | Catalog/docs only | Specialty drift before shared core. | Procedure/Treatment Templates |
| Material consumption exists operationally but not fully linked to clinical treatment semantics | `Material Consumption`, `Treatment Record` | Appointment/stock linked | Inventory can be correct while clinical procedure record is absent. | Procedure/Treatment Templates |
| ClinicalPlan exists but is not full workflow engine | `ClinicalPlan`, `Task`, `Episode-Based Care` | Episode-bound plan suggestion/confirm | Treating it as workflow engine too soon. | Task and Follow-up Foundation, later Episode-Based Care |
| Episode-Based Care remains future/deferred | `Episode-Based Care`, `Clinical Episode` | Object/routes/pages exist | Re-centering workflow around episodes before knowledge is stable. | Episode-Based Care Reactivation |

## 9. Safe implementation sequencing

1. Patient Knowledge Stabilization

   Purpose: učvrstiti Patient Workspace kao primarnu kliničku površinu.

   Depends on: `ClinicalDocument`, source badges, patient summary.

   Should not include yet: Episode-Based Care expansion, Workflow Engine, real AI provider.

   Implementation risk: summary se može pogrešno prikazati kao source of truth.

2. ClinicalDocument Review Hardening

   Purpose: učvrstiti review, reject, extraction pending i source metadata.

   Depends on: current ClinicalDocument registry.

   Should not include yet: separate Finding object unless justified.

   Implementation risk: miješanje raw documenta i findinga.

3. AI Suggestion Lifecycle

   Purpose: standardizirati pending/accepted/rejected/deferred/superseded AI states.

   Depends on: document review hardening.

   Should not include yet: real AI provider or autonomous decisions.

   Implementation risk: AI output izgleda službeno.

4. Patient Clinical Summary Alignment

   Purpose: uskladiti summary view s Patient Clinical Knowledge i official fact pravilima.

   Depends on: reviewed source-linked documents.

   Should not include yet: diagnosis registry.

   Implementation risk: PatientClinicalSummaryRecord postaje source of truth.

5. Clinical Readiness Gate Prototype

   Purpose: uvesti patient/service/procedure readiness bez miješanja s Operational Readinessom.

   Depends on: patient knowledge and document review.

   Should not include yet: legal/compliance claims or automatic cancellation.

   Implementation risk: lažni osjećaj medicinske sigurnosti.

6. Task and Follow-up Foundation

   Purpose: modelirati operativne sljedeće korake s vlasnikom i rokom.

   Depends on: open questions, clinical readiness, physician confirmation semantics.

   Should not include yet: full workflow engine.

   Implementation risk: task zamjenjuje clinical plan.

7. Medical Note and Patient Explanation Outputs

   Purpose: odvojiti professional documentation od patient-facing explanationa.

   Depends on: AI suggestion lifecycle and physician confirmation.

   Should not include yet: automatic sending to patients.

   Implementation risk: patient explanation bez potvrde.

8. Outcome Evidence Foundation

   Purpose: definirati i spremiti dokaz ishoda.

   Depends on: task/follow-up and document review.

   Should not include yet: automatic episode closure.

   Implementation risk: outcome kao slobodni tekst bez izvora.

9. Episode-Based Care Reactivation

   Purpose: vratiti episodes kao organizacijski sloj iznad znanja.

   Depends on: patient knowledge, findings/open questions, tasks, outcome evidence.

   Should not include yet: Workflow Engine.

   Implementation risk: epizoda postaje primarni izvor istine.

10. Procedure/Treatment Templates

    Purpose: standardizirati specialty procedure/treatment outputs.

    Depends on: shared core terminology and material consumption.

    Should not include yet: specialty protocols that bypass core.

    Implementation risk: duplicirani moduli i terminološki drift.

11. Specialty Protocols

    Purpose: dodati specialty-specific guidance/templates.

    Depends on: Procedure/Treatment Templates.

    Should not include yet: autonomous clinical decision support.

    Implementation risk: protokol izgleda kao medicinska odluka sustava.

12. Clinical Evidence Loop Hardening

    Purpose: povezati clinical need/risk, workspace, confirmed action, audit i outcome evidence.

    Depends on: prethodne faze.

    Should not include yet: production/compliance claims.

    Implementation risk: evidence loop se tretira kao certifikacija.

## 10. Naming risks found in current code

| Current name | File/context | Risk | Recommended future naming or documentation clarification |
| --- | --- | --- | --- |
| `/api/readiness`, `Readiness.tsx`, UI label `Spremnost` | Backend/frontend readiness | Može se pomiješati s future Clinical Readiness Gateom. | Dokumentirati kao `Operational Readiness`; buduće clinical endpoint nazvati npr. `clinical_readiness_status`. |
| `ClinicalPlan` | `domain.py`, routes, `EpisodeDetail.tsx` | Može izgledati kao full workflow engine. | Dokumentirati kao episode-bound plan suggestion/confirmation, not Workflow Engine. |
| `key_findings` | `ClinicalDocument`, `PatientClinicalSummaryRecord`, frontend types | Može se zamijeniti s future `Finding` objectom. | Pojasniti da su to extracted/reviewed strings, ne zaseban Finding object. |
| `PatientClinicalSummaryRecord` | `domain.py`, summary routes | Može se pogrešno shvatiti kao source of truth. | U docs/API opisima naglasiti summary view, source truth je source-linked knowledge. |
| `ai_summary`, `generated_by=ai_placeholder`, `ai_extraction_status` | ClinicalDocument/summary logic | Može zvučati kao real AI provider. | U UI/docs koristiti `AI placeholder draft` dok nema real providera; status prati prijedlog, ne medicinsku istinu. |
| `review_status` | `ClinicalDocument` | Eksplicitni lifecycle sada koristi `draft`, `extracted`, `needs_physician_review`, `reviewed`, `rejected`, `superseded`; `physician_reviewed` ostaje compatibility field. | Buduci task moze dodati supersede workflow ako audit pokaze potrebu. |
| `close_episode` | `/episodes/{id}/close` | Može djelovati kao formal Episode Closure. | Dokumentirati kao simple compatibility close, ne full closure. |
| `findings` form field in EpisodeDetail plan generation | `EpisodeDetail.tsx` | Uneseni tekst može se zamijeniti s reviewed Findingom. | Buduće labeliranje: `procedure_findings_text` ili "tekst nalaza za prijedlog". |
| `complete-with-consumption` | Appointment material route | Može spojiti completion i clinical outcome. | Jasno dokumentirati kao operational appointment/material completion. |

## 11. Documentation corrections recommended

Preporučene kasnije korekcije:

1. U `ASTRA_READINESS_MODEL.md` i README linkovima po potrebi dodati izraz `Operational Readiness` kada se pojavi budući Clinical Readiness Gate.
2. U dokumentima vezanim uz ClinicalPlan dodati napomenu da postojeći `ClinicalPlan` nije Workflow Engine.
3. U dokumentima vezanim uz ClinicalDocument dodati pojašnjenje da `key_findings` nisu zaseban `Finding` object.
4. U dokumentima vezanim uz EpisodeDetail/episode close pojačati da je `close_episode` compatibility funkcija, ne puni Episode Closure.

Nije pronađena potreba za širokim rewriteom.

Ako se u `PROGRAM_1_GLOSSARY.md` pojavi UTF-8 BOM marker u budućim alatima, sigurno ga je ukloniti kao tehničku korekciju bez promjene značenja. U ovom passu nije rađena takva izmjena.

## 12. Go / No-Go recommendation

Recommendation: Go with minor corrections.

Sljedeći arhitektonski korak:

`Program 1 - Implementation Phase A: Patient Knowledge Stabilization Plan`

Taj korak treba napraviti precizan plan implementacije za hardening Patient Clinical Knowledge i ClinicalDocument reviewa.

Ne preporučuje se direktna puna workflow implementacija.

Ne preporučuje se reaktivacija Episode-Based Carea prije stabilizacije patient knowledge sloja.

Ne preporučuje se uvođenje real AI providera, Workflow Enginea, clinical readiness gatea ili specialty protocols prije Phase A stabilizacije.
