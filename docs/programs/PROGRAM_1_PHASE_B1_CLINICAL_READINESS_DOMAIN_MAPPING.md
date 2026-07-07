# Program 1 Phase B1 - Clinical Readiness Domain Mapping

Status: documentation-only domain mapping

## 1. Svrha

Ovaj dokument mapira buduce Clinical Readiness koncepte na postojece ASTRA objekte i povrsine.

Ne uvodi backend kod, frontend kod, API endpoint, database model, migraciju ili UI ekran.

## 2. Mapping table

| Clinical Readiness concept | Existing ASTRA object/source | Current status | Future implementation candidate | Risk |
| --- | --- | --- | --- | --- |
| Patient | `Patient`, Patient Workspace | Current object | Anchor za svaki clinical readiness context | Slaba identifikacija moze dati pogresan kontekst |
| Appointment | `Appointment`, Appointment Workspace | Current object/view | Primarni anchor uz patient + service | Overloading appointment statusa clinical readinessom |
| Service | `Service`, catalog routes | Current object | Definira uslugu/proceduru/tretman za readiness rules | Service catalog nije procedure template engine |
| Provider | `Provider` | Current object | Odgovorna klinicka uloga ili owner | Mijesanje provider i user/role semantike |
| Room | `Room`, Reception Workspace | Current object | Resource readiness context | Soba nije klinicka odluka |
| ClinicalDocument | `ClinicalDocument` | Current source object | Reviewed source evidence za readiness items | Unreviewed documents ne smiju biti official source |
| Patient Clinical Knowledge | Patient source-linked knowledge helpers/UI | Current concept/view | Pregledani source-linked kontekst za readiness | Summary se ne smije tretirati kao source truth |
| Patient Clinical Summary | `PatientClinicalSummaryRecord` | Current summary view | Orientation-only context | Ne smije sam stvarati readiness fact |
| Open Question | source-linked open questions | Current concept | Readiness concern requiring review | Ne smije automatski postati task |
| Clinical Evidence Timeline | document evidence timeline | Current read-only audit view | Audit context for source/review events | Ne smije postati Outcome Evidence object |
| Reception Workspace | `Reception.tsx`, reception routes | Current view | Admin/arrival/identity verification context | Reception ne donosi klinicku odluku |
| Appointment Workspace | `AppointmentDetail.tsx` | Current view | Prvi kandidat za read-only Clinical Readiness Preview | Ne smije postati enforcing blocker prerano |
| Patient Workspace | `PatientDetail.tsx` | Current view | Source-linked clinical context | Ne smije se zamijeniti readiness checklistom |
| Operational Readiness | `/api/readiness`, `Readiness.tsx` | Current implemented concept | Mora ostati odvojeno | Naming collision s Clinical Readiness |
| AuditLog | `AuditLog`, audit service/routes | Current object | Future audit for confirmations/overrides | Audit event naming mora razlikovati AI/system/human |
| InventoryItem | `InventoryItem` | Current object | Material readiness source | Inventory availability nije clinical readiness sama po sebi |
| InventoryBatch | `InventoryBatch` | Current object | Batch/lot availability context | Treatment record semantics jos ne postoje |
| Material Consumption | stock movements/appointment materials | Current flow | Future readiness for planned materials | Ne smije stvarati clinical outcome |
| Consent | Documentation-only | Future concept | Required consent readiness item | Nema modela, zato ne implementirati blocker jos |
| Clinical Episode | `ClinicalEpisode` | Deferred compatibility object | Optional future grouping, not required | Requiring episode too early |
| ClinicalPlan | `ClinicalPlan` | Deferred compatibility concept | May later relate to decisions, not B1 | Ne smije postati readiness engine |
| Task | No generic task model | Future concept | Later operational follow-up | Readiness item nije task |
| Outcome Evidence | No object | Future concept | Later evidence of result/resolution | Timeline/audit nije outcome object |

## 3. Key mapping decisions

- Clinical Readiness treba biti anchored to Appointment + Service + Patient.
- Clinical Readiness smije citati Patient Clinical Knowledge.
- Clinical Readiness smije citati reviewed ClinicalDocuments.
- Clinical Readiness smije prikazati Open Questions kao readiness concerns.
- Clinical Readiness ne smije zahtijevati Clinical Episode.
- Clinical Readiness ne smije kreirati ClinicalPlan.
- Clinical Readiness ne smije kreirati Task.
- Clinical Readiness ne smije kreirati Outcome Evidence.
- Clinical Readiness ne smije koristiti unreviewed AI extraction kao source.
- Clinical Readiness ne smije koristiti Patient Clinical Summary kao source of truth.

## 4. Current vs future

| Concept | Current implemented | Future candidate | Deferred/no-go |
| --- | --- | --- | --- |
| Patient | current object | identity strengthening | real-data approval is No-Go |
| Appointment | current object | readiness preview anchor | do not overload appointment status |
| Service | current object | readiness rule context | no procedure template yet |
| Provider | current object | responsible role mapping | no automatic clinical authority |
| Room | current object | resource readiness context | no clinical decision |
| ClinicalDocument | current object | source evidence | no unreviewed source use |
| Patient Clinical Knowledge | current view/concept | official source-linked context | no unsourced facts |
| Patient Clinical Summary | current view | orientation only | no source-of-truth use |
| Open Question | current source-linked warning | readiness concern | no auto-task |
| Clinical Evidence Timeline | current view | audit context | no Outcome Evidence object |
| Operational Readiness | current object/view | remains separate | no clinical gate semantics |
| Clinical Readiness Gate | current documentation-only | future implementation candidate | no code in B1 |
| Consent | current documentation-only | future source/readiness item | no blocker before model |
| Clinical Episode | current/deferred | optional future grouping | no required episode |
| ClinicalPlan | current/deferred | future relation to decisions | no workflow engine |
| Task | future concept | later operational object | no task engine now |
| Outcome Evidence | future concept | later evidence object | no object now |

## 5. Mapping risks

- confusion with `/api/readiness`
- treating Open Question as Task
- treating Patient Clinical Summary as source truth
- requiring Clinical Episode too early
- making AI suggestion into readiness decision
- blocking procedure without override governance
- overloading Appointment status with clinical readiness
- making inventory availability look like clinical clearance
- using raw free text without source link
- hiding who is responsible for resolving an item

