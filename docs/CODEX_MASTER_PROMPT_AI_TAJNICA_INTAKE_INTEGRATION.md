# Codex master prompt — AI Tajnica Intake Integration Sprint

Use this prompt after `docs/CODEX_MASTER_PROMPT_PATIENT_KNOWLEDGE_HARDENING.md` has been reviewed and preferably implemented.

---

You are a senior healthcare integration architect, full-stack engineer, voice/email intake workflow designer, and clinical safety maintainer.

You are working on `radicdavor/ASTRA-Clinic-Core`.

Before changing code, read:

- `docs/ASTRA_ARCHITECTURE_BIBLE.md`
- `docs/ASTRA_DESIGN_SYSTEM.md`
- `docs/ASTRA_WORKSPACE_ARCHITECTURE.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/CODEX_MASTER_PROMPT_PATIENT_KNOWLEDGE_HARDENING.md`
- `docs/EPISODE_ENGINE_MVP.md`
- `docs/PILOT_RUNBOOK.md`

## Context

ASTRA has an external companion project called **AI Tajnica**.

AI Tajnica is intended to:

- receive patient phone calls
- collect reason for contact
- book appointments
- record what the patient needs
- receive patient emails with findings/reports
- forward documents for recognition/OCR/extraction
- create summaries for physician review

ASTRA Clinic Core must be able to receive this information safely.

The correct integration direction is not Episode Engine.

The correct integration direction is:

**Patient Clinical Knowledge Layer + Intake Queue**

AI Tajnica is an external intake source. It must not create official clinical knowledge without physician review.

---

# Sprint name

**AI Tajnica Intake Integration Sprint**

## Main objective

Create a safe intake boundary between external systems such as AI Tajnica and ASTRA Clinic Core.

The integration must support two flows:

1. Phone intake → appointment request / booking draft
2. Email/document intake → ClinicalDocument awaiting review

The system must clearly distinguish:

- patient-reported information
- AI-extracted information
- appointment request
- confirmed appointment
- uploaded document
- physician-reviewed knowledge

---

# Non-negotiable rules

- AI Tajnica must not create official clinical knowledge directly.
- AI Tajnica must not mark documents as physician-reviewed.
- AI Tajnica must not bypass patient duplicate checks.
- AI Tajnica must not create real production appointments unless explicitly allowed by a scoped API key and workflow state.
- Intake records must be reviewable.
- Every external document must become a `ClinicalDocument` or an intake item that can become one.
- Real patient data remains forbidden in demo mode.
- Do not implement real telephony provider integration in this sprint.
- Do not implement real Gmail/IMAP integration in this sprint.
- Do not implement real OCR provider in this sprint.
- Do not implement real AI provider in this sprint.
- Use placeholders/contracts and API boundaries.
- Keep Episode Engine deferred from primary workflow.

---

# Critical review of current state

## What exists

- Patient identity and duplicate awareness.
- Appointment creation with resolved patient search.
- ClinicalDocument model and endpoints.
- Upload placeholder and raw text storage.
- AI extraction placeholder.
- Physician review/reject flow.
- Patient clinical summary based only on reviewed documents.
- Readiness warning for documents awaiting review.
- API key infrastructure.

## What is missing for AI Tajnica

1. No dedicated intake object exists.
2. There is no safe staging area for phone/email inputs before they become appointments or documents.
3. There is no explicit source system field for AI Tajnica events.
4. Appointment requests and confirmed appointments are not separated enough for external intake.
5. E-mail attachments/documents should enter as unreviewed ClinicalDocuments with source metadata.
6. Patient matching needs a review step for uncertain matches.
7. Readiness should show intake items awaiting review.
8. Audit should clearly say whether data came from user, API key, or AI Tajnica.

This sprint should build the boundary, not the full AI Tajnica product.

---

# Phase 1 — Document the integration contract

Create:

`docs/AI_TAJNICA_INTAKE_CONTRACT.md`

Required sections:

1. Purpose
2. AI Tajnica as external intake source
3. Phone call intake flow
4. E-mail/document intake flow
5. Patient matching rules
6. Appointment request vs confirmed appointment
7. ClinicalDocument creation rules
8. Physician review requirement
9. API key/scopes
10. Demo-mode safety
11. What is deliberately not implemented yet

Must state:

- AI Tajnica can suggest and stage.
- ASTRA decides through reviewed workflow.
- Physician/admin confirmation is required for official clinical knowledge.
- Uncertain patient identity must not silently merge into an existing patient.

Acceptance criteria:

- Document exists.
- README links to it.
- It references Patient Clinical Knowledge Layer.

---

# Phase 2 — Add IntakeRecord model

Create a generic staging object:

`IntakeRecord`

Suggested fields:

- id
- source_system
- source_channel
- external_reference
- patient_match_status
- matched_patient_id
- proposed_first_name
- proposed_last_name
- proposed_date_of_birth
- proposed_oib
- proposed_phone
- proposed_email
- reason_for_contact
- requested_service_id
- requested_provider_id
- requested_room_id
- requested_date
- requested_time
- urgency
- raw_transcript
- raw_email_subject
- raw_email_from
- raw_email_body
- ai_summary
- status
- created_appointment_id
- created_document_id
- reviewed_by
- reviewed_at
- created_at
- updated_at

Suggested `source_system`:

- `ai_tajnica`
- `manual`
- `api`
- `email_placeholder`

Suggested `source_channel`:

- `phone`
- `email`
- `web`
- `manual`

Suggested `patient_match_status`:

- `unmatched`
- `possible_match`
- `matched`
- `new_patient_proposed`
- `rejected`

Suggested `status`:

- `new`
- `needs_review`
- `ready_to_schedule`
- `scheduled`
- `converted_to_document`
- `rejected`
- `archived`

Rules:

- IntakeRecord is not official clinical knowledge.
- IntakeRecord is a staging object.
- IntakeRecord can later create an appointment or ClinicalDocument.
- All conversion actions must be audited.

Acceptance criteria:

- Model exists.
- Migration exists.
- Schemas exist.
- Demo seed can create at least one phone and one email intake record.

---

# Phase 3 — Add API scopes and permissions

Add permissions:

- `intake.read`
- `intake.write`
- `intake.review`

For API keys, define recommended AI Tajnica scopes:

- `intake.write`
- optionally `patients.read` for matching if explicitly allowed
- optionally `appointments.write` only if direct booking is allowed later
- not `clinical_documents.review`
- not `patients.write` unless explicit controlled workflow exists

Seed admin/physician roles with review/read as appropriate.

Acceptance criteria:

- API keys can be scoped for intake-only behavior.
- AI Tajnica cannot review clinical documents.

---

# Phase 4 — Add intake API endpoints

Add endpoints:

- `GET /api/intake-records`
- `POST /api/intake-records`
- `GET /api/intake-records/{id}`
- `PATCH /api/intake-records/{id}`
- `POST /api/intake-records/{id}/match-patient`
- `POST /api/intake-records/{id}/create-patient`
- `POST /api/intake-records/{id}/create-appointment`
- `POST /api/intake-records/{id}/create-clinical-document`
- `POST /api/intake-records/{id}/reject`

Validation:

- cannot create appointment unless matched_patient_id exists or create-patient step was completed
- cannot create appointment from ambiguous patient text
- cannot create ClinicalDocument without patient
- document created from intake must be physician_reviewed=false
- document source_type should be `external` or `uploaded`
- document origin should mention `AI Tajnica` or source channel
- every conversion writes audit

Acceptance criteria:

- intake can be staged
- reviewer can match patient
- reviewer can create appointment
- reviewer can create ClinicalDocument
- nothing becomes physician-reviewed automatically

---

# Phase 5 — Patient matching support

Use existing patient search and possible duplicates.

For `match-patient`:

- accept a patient_id selected by reviewer
- verify patient exists
- set patient_match_status=`matched`
- set matched_patient_id
- audit the match

For automatic helper only:

- endpoint may return possible matches based on name/OIB/phone/email
- do not automatically choose if multiple candidates
- if exact OIB match exists, suggest strongly but still record trace

Acceptance criteria:

- uncertain identity remains reviewable
- reviewer chooses final match

---

# Phase 6 — Phone intake workflow

Phone intake should stage appointment request data.

IntakeRecord fields used:

- patient proposed identity
- reason_for_contact
- requested_service_id if known
- requested date/time if known
- urgency
- raw_transcript
- ai_summary

Frontend reviewer should see:

- caller identity
- possible patient matches
- reason for call
- requested service/time
- AI summary
- actions:
  - match existing patient
  - create new patient
  - create appointment
  - reject/archive

Do not build real telephony.

Acceptance criteria:

- a phone intake can become a confirmed appointment only after review/match

---

# Phase 7 — Email/document intake workflow

Email intake should stage documents.

IntakeRecord fields used:

- raw_email_subject
- raw_email_from
- raw_email_body
- attachment metadata if implemented as simple text field
- proposed patient identity if extractable
- ai_summary

Conversion to ClinicalDocument:

- patient must be matched
- create ClinicalDocument with source_type=`external` or `uploaded`
- document_type determined by reviewer or AI suggestion
- raw_text from OCR/email placeholder
- ai_summary optional
- physician_reviewed=false
- status remains awaiting review

Acceptance criteria:

- email reports become unreviewed ClinicalDocuments with source metadata
- Patient summary does not include them until review

---

# Phase 8 — Frontend Intake Queue

Add pages:

- `frontend/src/pages/IntakeRecords.tsx`
- `frontend/src/pages/IntakeRecordDetail.tsx`

Routes:

- `/intake`
- `/intake/:id`

Navigation:

- Add `Ulazni zahtjevi` or `Intake` to AppShell.

List should show:

- created_at
- source channel
- proposed patient
- reason/contact
- status
- patient match status
- link to detail

Detail should show:

- source info
- patient identity proposal
- possible matches
- raw transcript/email
- AI summary
- requested service/time
- review actions
- created appointment/document links
- audit timeline

Use:

- Workspace components
- ActionButton
- HelpHint
- patientIdentity helper

Acceptance criteria:

- receptionist/admin can review staged AI Tajnica items
- conversions are visible and auditable

---

# Phase 9 — Readiness integration

Update `/api/readiness`:

Add check:

- key: `intake_records_review`
- label: `Ulazni zahtjevi`
- status: warning if records in `new` or `needs_review`
- count: pending intake records
- decision_impact: review
- target_path: `/intake?status=needs_review`
- target_label: `Pregledaj ulazne zahtjeve`
- message explains these are staged and not official until reviewed

Acceptance criteria:

- readiness surfaces AI Tajnica backlog

---

# Phase 10 — Audit readability

Audit labels should clearly distinguish:

- intake created
- patient matched
- patient created from intake
- appointment created from intake
- document created from intake
- intake rejected

Update AuditTimeline label map if needed.

Acceptance criteria:

- reviewer can reconstruct what AI Tajnica sent and what human confirmed

---

# Phase 11 — Demo seed

Seed demo intake records:

1. Phone call:
   - patient asks for gastroscopy because of reflux symptoms
   - possible existing patient match
   - requested service: gastroscopy or consultation

2. Email/document:
   - patient sends external gastroscopy report text
   - unmatched or possible matched patient
   - can convert to ClinicalDocument

Acceptance criteria:

- demo immediately shows intake queue value

---

# Phase 12 — Tests

Backend tests:

- create intake record with API key scope `intake.write`
- list intake requires `intake.read`
- match patient requires `intake.review`
- cannot create appointment without matched patient
- create appointment from matched intake
- create ClinicalDocument from matched email intake
- created ClinicalDocument is not physician-reviewed
- Patient summary excludes unreviewed document from intake
- readiness counts pending intake records
- audit events exist for conversions

Frontend smoke/static:

- `/intake` route exists
- `/intake/:id` route exists
- AppShell contains intake navigation
- Intake detail contains possible matches section
- Intake detail contains create appointment action
- Intake detail contains create ClinicalDocument action
- Readiness links to `/intake?status=needs_review`

Acceptance criteria:

- existing v0.1-pilot workflow remains intact
- tests/smoke/typecheck/build pass

---

# Phase 13 — Documentation updates

Update:

- `README.md`
- `docs/PILOT_RUNBOOK.md`
- `docs/ASTRA_READINESS_MODEL.md`
- `docs/ASTRA_OPERATIONAL_EVIDENCE_LOOP.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/PATIENT_CLINICAL_KNOWLEDGE_LAYER_MVP.md` if it exists

Create:

`docs/AI_TAJNICA_INTAKE_MVP.md`

Include:

- what is implemented
- what is placeholder
- API key scope recommendations
- phone intake flow
- email/document intake flow
- human review requirement
- relationship to ClinicalDocument and Patient Summary
- what AI Tajnica must not do

---

# Suggested commit sequence

1. `docs: add AI Tajnica intake contract`
2. `feat: add intake record model and schemas`
3. `feat: add intake permissions and scoped API key guidance`
4. `feat: add intake record API endpoints`
5. `feat: add patient matching workflow for intake`
6. `feat: convert phone intake to appointment after review`
7. `feat: convert email intake to clinical document after review`
8. `feat: add intake queue frontend pages`
9. `feat: add readiness warning for pending intake records`
10. `feat: improve audit labels for intake conversions`
11. `seed: add demo AI Tajnica intake records`
12. `test: cover intake API and conversion safety`
13. `test: add frontend smoke for intake queue`
14. `docs: document AI Tajnica intake MVP`

---

# Definition of done

This sprint is done when:

- AI Tajnica has a safe intake boundary.
- Phone call information can be staged as IntakeRecord.
- Email/document information can be staged as IntakeRecord.
- Reviewer can match patient.
- Reviewer can create appointment from matched intake.
- Reviewer can create unreviewed ClinicalDocument from matched email/document intake.
- Patient Summary does not include intake-derived document until physician review.
- Readiness shows pending intake review.
- Audit distinguishes external AI intake from human confirmation.
- Episode Engine remains deferred from primary workflow.
- Tests and smoke pass.

The design principle is:

**AI Tajnica may collect and stage information. ASTRA only treats it as official after human review and source-linked confirmation.**
