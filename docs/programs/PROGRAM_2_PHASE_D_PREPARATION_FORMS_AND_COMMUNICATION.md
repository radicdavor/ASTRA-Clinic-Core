# Program 2 — Phase D: Preparation, Forms and Communication

## Status

Phase D is implemented as an additive backend contract. It does not connect live email or SMS providers and it does not make clinical decisions.

## Canonical ownership

- `PreparationPlanTemplate` is a versioned, human-approved catalog entry for one procedure type.
- `JourneyPreparation` is the single preparation assignment for a patient journey and stores the state of each required item.
- `PatientFormTemplate` is a versioned, human-approved form definition.
- `JourneyForm` records the exact template version and submitted answers for one journey.
- `DocumentRequest` records a required or optional source document without duplicating the document itself.
- `JourneyReminder` is scheduling intent; `CommunicationEvent` is the resulting delivery attempt.

The `PatientJourney` aggregate remains the canonical workflow state. These records provide evidence and detail; they do not create a parallel workflow.

## Preparation contract

A plan contains patient-facing instructions, procedure type, version, structured requirements and a reminder schedule. A plan can be assigned only when it is active and has a human approval timestamp. Default reminders are scheduled two days and one day before the appointment unless the approved template specifies another schedule.

Requirement states are `confirmed`, `not_confirmed`, `not_applicable`, `requires_clinician_review` and `blocked`.

`requires_clinician_review` and `blocked` set preparation to `review_required`. Software does not automatically clear either state. Completion requires every configured requirement to be explicitly confirmed or marked not applicable by an authorized human.

## Forms and document requests

Forms are stored against an immutable template version. Submission records answers and completion time, but completion is not clinical approval. Document requests identify the expected source material; Phase E links received source documents through the canonical ingestion pipeline.

## Communication and reminders

Supported contract channels are email, SMS, web portal and manual delivery. A communication event records channel, approved template key, queue/sent/delivery state, timestamps, failure reason and correlation ID.

The current `DemoDeliveryProvider` is deterministic and local. It changes `QUEUED` to `SENT` only. It never claims `DELIVERED`, and it performs no external network call. Live provider credentials, live SMS and live email remain deferred and require separate explicit authorization.

## RBAC and audit

- `preparation.assign`: physician, nurse and reception staff
- `preparation.review`: physician only, plus administrator
- `documents.request`: physician, nurse and reception staff

Template creation, assignment, requirement review, form request/completion, document request and reminder dispatch create audit records. Journey-local events additionally preserve the operational timeline.

## Safety boundary

Approved templates may convey reviewed instructions but may not autonomously diagnose, approve fasting, give medication changes, clear sedation, mark the patient clinically ready or resolve a clinical blocker. Those actions remain human-owned.
