# ASTRA Clinical Model

Status: Episode Engine Foundation

ASTRA Clinical Model defines how medicine exists inside ASTRA Clinic Core during demo/pilot development. It is not production approval, EMR certification, medical-device certification or permission to use real patient data.

## 1. Purpose

The clinical model gives ASTRA one language for clinical context.

Its first structural unit is Clinical Episode: a patient-centered story around a problem, goal, treatment path or follow-up process.

ASTRA organizes, documents and connects context. The clinician decides.

## 2. Patient

Patient is the person.

The patient is identified by name, date of birth, OIB when available, phone and e-mail. A patient is not only a number, and no appointment should be created for an unknown patient.

## 3. Clinical Episode

Clinical Episode is the clinical story.

It is not an appointment, diagnosis, invoice or workflow. It gathers the context around why care is happening and what remains open.

Examples include GERB/reflux follow-up, H. pylori eradication, colon polyp surveillance, post-polypectomy follow-up, metabolic care, aesthetic treatment or preventive check-up.

## 4. Problem

A problem is the reason a story exists.

In the MVP, the problem is represented only through episode title, type, summary and notes. ASTRA does not yet maintain a formal problem list.

## 5. Diagnosis

Diagnosis is a clinical conclusion made by a qualified clinician.

Episode Engine does not create diagnoses, code diagnoses or imply diagnostic certainty.

## 6. Goal Of Care

Goal of care describes what the episode is trying to achieve: symptom control, surveillance, follow-up, prevention, treatment completion or administrative closure.

In the MVP, goals are written in the episode summary/notes. Structured goal tracking is future work.

## 7. Plan

Plan is the clinician-approved direction for care.

In the AI Assisted Clinical Plan version, ASTRA stores a structured `ClinicalPlan`.

AI may prepare a draft suggestion, but the official plan exists only after physician confirmation.

The confirmed plan becomes the active state of the Clinical Episode. Unconfirmed AI suggestions must never be displayed as official clinical direction.

Workflow Engine is still future operational automation and must not be inferred from the current plan model.

## 8. Appointment

Appointment is an event in time.

It connects patient, provider, room, service and status. An appointment may optionally belong to a Clinical Episode. Existing appointments can remain without an episode during the first version.

## 9. Follow-Up

Follow-up is the continuation of an episode after an event.

The MVP can describe follow-up in notes and can link future appointments to the same episode. It does not implement task automation, reminders or clinical protocols.

## 10. Result/Outcome

Result/outcome is the human-reviewed state at the end of an episode.

In the MVP, closing an episode sets status to `completed` and records an end date when missing. It does not certify clinical success or failure.

## 11. Episode Status Lifecycle

Initial statuses are intentionally simple:

- `open`
- `active`
- `waiting`
- `completed`
- `cancelled`
- `archived`

`open`, `active` and `waiting` represent ongoing clinical context. `completed`, `cancelled` and `archived` are terminal or inactive states.

## 12. Relationship Between Episode, Workflow Engine, Knowledge Engine And AI

Episode is the clinical story.

Workflow Engine is future operational automation that may later attach tasks, steps and responsibilities to an episode.

Knowledge Engine is future domain reasoning that may later provide structured medical knowledge, guidelines or safety checks.

AI is a future assistant layer. It may suggest, organize, remind or summarize, but it must not hide uncertainty, invent data, make medical decisions or change critical data without permission.

In the current plan MVP, AI suggestion is local and controlled. It is a preparation layer, not an autonomous clinical actor.

## 13. What ASTRA Must Not Do

ASTRA must not:

- use real patient data in demo/pilot mode
- create unknown-patient appointments
- present an episode as a diagnosis
- make medical decisions
- imply production readiness
- implement real Croatian fiscalization through Episode Engine
- silently automate clinical workflow
- add documents, labs, prescriptions or new clinical modules inside this sprint

## 14. Examples

### GERB Episode

Patient has reflux symptoms and follow-up appointments. The episode title may be `GERB/refluks pracenje`, type `gastroenterology`, status `active`, summary describing demo follow-up context, and appointments linked over time.

### Colon Polyp Surveillance Episode

Patient has a surveillance story after colonoscopy/polyp finding. The episode may track future control appointments and notes, but it does not implement guideline calculation or pathology documents in this MVP.

### Aesthetic Medicine Episode

Patient has an aesthetic treatment plan. The episode groups consultation and treatment appointments. It does not add a new aesthetic clinical module, consent documents or automated protocols in this sprint.
