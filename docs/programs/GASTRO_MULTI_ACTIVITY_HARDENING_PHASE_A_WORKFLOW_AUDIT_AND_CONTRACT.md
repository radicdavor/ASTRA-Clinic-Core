# Gastro Multi-Activity Hardening — Phase A Workflow Audit and Contract

## Repository baseline

- Repository: `radicdavor/ASTRA-Clinic-Core`
- Branch: `main`
- Starting commit: `8b828657dc5562c134011be6235e613eb31c2dfa`
- Git state at opening: clean and aligned with `origin/main`
- Alembic head: `0051_activity_billing`
- Existing aggregate: one `PatientJourney` per physical arrival with multiple `JourneyActivity` records

## Current-state audit

| Area | Current implementation | Gap to close |
|---|---|---|
| Package booking | Published package APIs and activity materialization exist | No non-mutating schedule preview or receptionist package UI; materialization loops without an explicit savepoint contract |
| Preparation | Journey-level preparation template and checklist | No activity provenance, deduplication or contradiction detection |
| Clinical forms | Versioned definitions, bindings, instances, revisions and signing | List-like fields are comma-separated text; no controlled repeatable groups |
| Gastroscopy/colonoscopy | Initial controlled field catalogs | Findings, polyps, biopsies, clips and specimens are not repeatable structured records |
| Interventions | Structured backend record with a small inline frontend editor | Specimen creation uses `window.confirm` and `window.prompt` |
| Signed reports | Immutable application workflow and exact stored rendered version | No content hash or database trigger preventing update/delete |
| Delivery | Local-demo queue and history | Uses broad document-review permission and arbitrary prompt-entered recipient |
| Pathology | Structured cases/specimens, result link and clinician review | Closure may occur without a structured communication disposition |
| Legacy encounter | Existing journey encounter remains readable/writable | Activity-enabled journeys still expose a parallel clinical write path |
| Demo | Seeded two-activity arrival | No API-driven package scenario with consultation, gastroscopy and colonoscopy |
| Browser evidence | Dashboard/workspace reviewed | Full gastro package, preparation, specimens, reports, billing and follow-up not yet proven |

## Canonical synthetic scenario

Synthetic patient:

- Name: `Sintetički Gastro Paket`
- E-mail: `synthetic.gastro.package@example.invalid`
- No real identifier or real clinical data

One coordinated arrival:

1. `08:00–08:30` — First gastroenterology consultation, consultation room
2. `08:40–09:10` — Gastroscopy, endoscopy room 1
3. `09:20–10:00` — Colonoscopy, endoscopy room 2

Expected documentation:

- Consultation: reason, anamnesis, examination, opinion/recommendations, diagnoses, therapy and follow-up
- Gastroscopy: incomplete cardia closure, mild distal esophagitis, antral erythema, antrum and corpus biopsies, no immediate complication
- Colonoscopy: caecal completion, terminal ileum visualization, preparation quality, two polyps, cold-snare polypectomy, second biopsy/polypectomy, clip, withdrawal time and no immediate complication

Expected structured clinical records:

- at least two gastroscopy biopsy interventions
- at least two colon polyp records
- one cold-snare polypectomy
- one additional biopsy or polypectomy
- one clip placement
- at least three uniquely labelled pathology specimens
- one pathology case per source activity unless explicitly consolidated by a future approved policy

Expected operational outcome:

- one check-in
- aggregated preparation retaining activity provenance
- three completed activities
- three separately signed reports
- activity-linked consumables
- one invoice with activity-specific source keys
- full payment and physical visit closure
- pathology remains an open post-visit follow-up
- later original result document, clinician review, approved patient explanation, explicit communication disposition and audited closure

## Source-of-truth rules

- `PatientJourney` owns the arrival, check-in, coordinated billing and physical closure.
- `JourneyActivity` owns service, schedule, room, clinician and activity state.
- `ClinicalFormInstance` is the write source for new activity-enabled clinical documentation.
- `ProcedureIntervention` and `PathologySpecimen` are the structured source for interventions and specimens; form snapshots may reference them but must not create divergent duplicates.
- `SignedClinicalReport` preserves the immutable signed snapshot; later correction creates a new version.
- Original pathology source documents remain the diagnostic source of truth.
- Patient communication requires a structured human-owned disposition.

## Safety boundaries

- No autonomous diagnosis, treatment, pathology interpretation or patient communication.
- No real data or production provider.
- No live e-mail, SMS, OCR, AI secretary, public booking, pathology integration, fiscalization or payment terminal.
- Human gastroenterology usability evaluation remains future work and must not be claimed by automated evidence.
