# Codex master prompt — Patient Clinical Knowledge Layer Hardening Sprint

Use this prompt in Codex after commit `92ada40 Defer episode engine from primary workflow`.

---

You are a senior healthcare domain architect, full-stack engineer, AI workflow designer, and clinical safety maintainer.

You are working on `radicdavor/ASTRA-Clinic-Core`.

Before changing code, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/ASTRA_DESIGN_SYSTEM.md`
- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/EPISODE_ENGINE_MVP.md`
- `docs/PILOT_RUNBOOK.md`
- latest commit `92ada40 Defer episode engine from primary workflow`

## Context

Episode Engine was implemented experimentally, then correctly deferred from the primary workflow.

The primary clinical direction is now:

**Patient Clinical Knowledge Layer**

The purpose is not to organize the patient around artificial episodes.

The purpose is to answer, immediately when opening a patient:

> What do we know about this patient, what remains unresolved, and where did each statement come from?

The codebase already includes important foundations:

- `ClinicalDocument` domain object
- `/api/clinical-documents` endpoints
- upload placeholder
- AI extraction placeholder
- physician review / reject summary endpoints
- `/api/patients/{patient_id}/clinical-summary`
- `ClinicalDocuments.tsx`
- `ClinicalDocumentDetail.tsx`
- source badge pattern
- readiness warning for documents awaiting review
- Episode Engine marked experimental/deferred

This sprint must harden and deepen that direction.

---

# Sprint name

**Patient Clinical Knowledge Layer Hardening Sprint**

## Main objective

Make the Patient Workspace a trustworthy clinical knowledge surface, where every AI-derived statement is source-linked, physician-reviewed, and operationally visible.

The system must make it impossible to confuse:

- raw uploaded/scanned text
- AI-extracted suggestion
- physician-reviewed clinical knowledge
- official patient summary

---

# Non-negotiable rules

- Do not re-promote Episode Engine to primary workflow.
- Do not require appointments to have episodes.
- Do not add Workflow Engine.
- Do not add Knowledge Engine.
- Do not add AI automation that updates official knowledge without physician review.
- Do not integrate a real OCR provider in this sprint.
- Do not integrate a real AI provider in this sprint.
- Do not enable real patient data.
- Do not implement real Croatian fiscalization.
- Keep demo warnings visible.
- Keep source transparency mandatory.
- Every official clinical summary item must trace to at least one reviewed ClinicalDocument.

---

# Critical review of current state

## What is good

1. ClinicalDocument exists and has the right strategic role.
2. Upload is implemented as a placeholder with metadata and raw text.
3. AI extraction placeholder exists and is explicitly not official until review.
4. Physician review exists.
5. Patient clinical summary only uses reviewed documents.
6. Readiness now points to `/clinical-documents` rather than `/episodes`.
7. Episode Engine is marked experimental/deferred.

## What is still weak

1. Patient Clinical Summary is still mostly keyword/rule-based and may produce duplicated or low-value items.
2. There is no separate persistent `PatientKnowledgeFact` object yet.
3. Source links exist at the item level in the API shape, but the UI must make them impossible to miss.
4. Document review is binary; it does not yet support editing extracted facts before confirming.
5. Upload form still uses raw Patient ID rather than patient search in some places.
6. OCR and AI are placeholders, but the boundary contract should be clearer.
7. Readiness warns about unreviewed documents, but the cockpit should help route directly to documents awaiting review.
8. Episode pages still exist and may confuse users if surfaced too strongly.

This sprint should address those weaknesses without building a full EMR.

---

# Phase 1 — Create Patient Clinical Knowledge Model documentation

Create:

`docs/ASTRA_PATIENT_CLINICAL_KNOWLEDGE_MODEL.md`

Required sections:

1. Purpose
2. Why Patient Knowledge comes before Episode Engine
3. ClinicalDocument
4. AI extraction suggestion
5. Physician review
6. Official patient knowledge
7. Source-linked summary
8. Unresolved findings / open questions
9. External documents and fragmented care
10. OCR placeholder boundary
11. AI placeholder boundary
12. What is deliberately not implemented yet
13. Future migration path toward Episode Engine, Workflow Engine, and Knowledge Engine

Must state clearly:

- AI extracted knowledge is never official until physician-reviewed.
- Every official fact must have a source.
- External documents are first-class clinical inputs.
- Episode Engine is deferred until patient-level knowledge is stable.

Acceptance criteria:

- Document exists.
- README links to it.
- `docs/EPISODE_ENGINE_MVP.md` references it as the primary clinical direction.

---

# Phase 2 — Harden ClinicalDocument status model

Current `physician_reviewed` boolean is useful, but UI and API need clearer states.

Add or derive document workflow status:

- `uploaded`
- `extraction_pending`
- `ai_extracted`
- `reviewed`
- `summary_rejected`
- `archived`

Preferred minimal approach:

- Keep existing database columns if changing schema is too large.
- Add computed field to `ClinicalDocumentOut`:
  - `review_status`

Rules:

- no raw_text and no ai_summary and not reviewed -> `uploaded`
- raw_text exists and ai_summary missing and not reviewed -> `extraction_pending`
- ai_summary exists and not reviewed -> `ai_extracted`
- physician_reviewed true -> `reviewed`
- summary rejected and not reviewed -> `summary_rejected` if trackable; otherwise document as deferred

Acceptance criteria:

- API returns `review_status` or equivalent.
- UI shows clear status badges.
- Users can distinguish uploaded, extracted, reviewed, rejected.

---

# Phase 3 — Add editable extraction review before physician confirmation

ClinicalDocumentDetail currently shows AI summary, key findings and recommendations, then allows review/reject.

Improve it so the physician can edit extracted structured fields before confirming.

Frontend:

- AI summary editable textarea
- key findings editable multiline list
- recommendations editable multiline list
- Save extraction edits button
- Confirm review button
- Reject summary button

Backend:

- existing PATCH endpoint may be enough
- ensure PATCH resets `physician_reviewed=false`
- confirming after edit sets reviewed metadata

Rules:

- confirmed summary uses edited values
- audit records edit before confirmation
- rejected summary does not enter patient summary

Acceptance criteria:

- physician can correct AI extraction before review
- corrected extraction becomes source for Patient Summary

---

# Phase 4 — Strengthen Patient Workspace Clinical Knowledge sidebar

Patient Workspace must show clinical knowledge first, not episodes.

Ensure PatientDetail includes a visible Clinical Knowledge section/sidebar with:

- known problems
- completed procedures
- pathology
- laboratory
- imaging
- current therapy
- open questions
- latest recommendations
- awaiting review count

Every item must render source badges.

Each source badge links to:

`/clinical-documents/{document_id}`

Add empty states:

- “Nema pregledanih dokumenata”
- “Postoje dokumenti koji čekaju liječnički pregled”
- “Dodaj dokument” link with patient context

Acceptance criteria:

- Opening a patient answers: what do we know, what is unresolved, and what are the sources?
- No summary item appears without at least one source.

---

# Phase 5 — Replace Patient ID raw entry in document upload with patient search

ClinicalDocuments upload currently accepts raw patient ID. This is acceptable internally but weak for real use.

Implement patient search selection similar to AppointmentForm:

- search by name/OIB/phone/email
- result cards with identity details
- selected patient card
- submit disabled until patient selected
- if opened with `?patient_id=`, preselect that patient if possible

Keep raw patient ID fallback only if necessary for dev/debug, but do not make it the primary UI.

Acceptance criteria:

- document upload uses resolved patient selection
- no ambiguous free-text patient assignment

---

# Phase 6 — Readiness cockpit: documents awaiting review deep link

Readiness already counts documents awaiting review.

Improve readiness check:

- key: `clinical_documents_review`
- target_path: `/clinical-documents?physician_reviewed=false`
- target_label: `Pregledaj dokumente`
- decision_impact: `review`
- message includes count

Frontend Readiness:

- target link preserves query params
- detail panel explains that unreviewed documents do not enter official patient summary

Acceptance criteria:

- one click from readiness opens documents awaiting review

---

# Phase 7 — Introduce source coverage validation for Patient Summary

Backend:

Add tests or runtime guard ensuring every `PatientKnowledgeItem` in `PatientClinicalSummary` has at least one source.

If a summary category item has no source, it must not be returned.

Add tests:

- reviewed document contributes source-linked item
- unreviewed document does not contribute
- item without source is not possible

Acceptance criteria:

- official summary cannot contain unsourced item

---

# Phase 8 — Reduce duplicate/low-value Patient Summary items

Current summary may collect duplicate findings from multiple fields.

Add simple deduplication:

- normalize item text lower/trim
- deduplicate within each category
- if same text has multiple sources, merge sources

Do not build complex NLP.

Acceptance criteria:

- summary is cleaner
- duplicate statements merge source badges rather than repeat rows

---

# Phase 9 — ClinicalDocument audit readability

Audit should clearly distinguish:

- document uploaded
- AI extraction generated
- extraction edited
- physician reviewed
- AI summary rejected

Update audit labels if needed in `AuditTimeline` human-readable label map.

Acceptance criteria:

- Document timeline is understandable to physician/admin user

---

# Phase 10 — Keep Episode Engine hidden/deferred

Ensure:

- AppShell does not show Epizode as primary nav
- Readiness does not warn/block missing episodes
- AppointmentForm does not push users to create episodes
- Pilot Runbook says leave `Bez epizode` unless explicitly testing legacy/deferred episode compatibility
- Episode docs clearly say experimental/deferred

Acceptance criteria:

- primary workflow is patient knowledge, not episodes

---

# Phase 11 — Tests and smoke

Backend tests:

- create/upload clinical document
- update raw text resets review status
- extraction generates AI suggestion but not official summary
- review makes document eligible for patient summary
- reject removes AI summary and keeps it out of official summary
- patient clinical summary uses reviewed documents only
- every summary item has source
- duplicate summary items are merged
- readiness link for unreviewed documents uses query param

Frontend smoke/static:

- ClinicalDocuments page exists
- ClinicalDocumentDetail page exists
- PatientDetail includes clinical knowledge summary first
- SourceBadge links to clinical document detail
- upload form uses patient search/selection
- readiness points to `/clinical-documents?physician_reviewed=false`
- AppShell includes Dokumenti
- AppShell does not include Epizode as primary nav

Acceptance criteria:

- backend tests pass
- frontend smoke/typecheck/build pass
- GitHub CI remains green

---

# Phase 12 — Documentation updates

Update:

- `README.md`
- `docs/PILOT_RUNBOOK.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- `docs/EPISODE_ENGINE_MVP.md`

Create or update:

- `docs/PATIENT_CLINICAL_KNOWLEDGE_LAYER_MVP.md`

Document:

- what works now
- what is placeholder
- how physician review works
- why sources are mandatory
- why OCR/AI are placeholders
- what is deferred

---

# Suggested commit sequence

1. `docs: add patient clinical knowledge model`
2. `feat: expose clinical document review status`
3. `feat: make extracted document knowledge editable before review`
4. `feat: strengthen patient workspace clinical knowledge sidebar`
5. `feat: use patient search for clinical document upload`
6. `feat: deep link readiness to documents awaiting review`
7. `test: require source coverage in patient clinical summary`
8. `feat: deduplicate patient clinical summary items`
9. `feat: improve clinical document audit labels`
10. `chore: keep episode engine deferred from primary workflow`
11. `test: harden clinical document and summary workflows`
12. `docs: document patient clinical knowledge layer MVP`

---

# Definition of done

This sprint is done when:

- Patient Clinical Knowledge Model document exists.
- ClinicalDocument review status is clear.
- Physician can edit AI-extracted fields before confirming.
- Patient Workspace shows source-linked summary first.
- Document upload uses resolved patient selection.
- Readiness deep-links to unreviewed documents.
- Patient Summary contains only reviewed, sourced items.
- Duplicate summary items are merged.
- ClinicalDocument audit is readable.
- Episode Engine remains experimental/deferred and hidden from primary workflow.
- Tests/smoke/build pass.

The design principle is:

**ASTRA must first know what is known about the patient, and exactly where each fact came from. Everything else comes later.**
