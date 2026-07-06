# Episode Engine MVP

Status: experimental/deferred. Foundation exists for compatibility with earlier demo work, but Episode Engine is paused.

Primary direction is now Patient Clinical Knowledge Layer. Do not continue building episode-centric workflows until patient-centric knowledge, source-linked summaries and document review are stable.

Episode Engine adds Clinical Episode as an experimental clinical story object in ASTRA Clinic Core.

## What It Does Now

- Adds `ClinicalEpisode` as a backend model.
- Links episodes to patients.
- Allows appointments to optionally link to an episode.
- Prevents linking an appointment to an episode from another patient.
- Adds episode list, create page and Episode Workspace.
- Episode pages remain available by direct route, but episodes are hidden from primary navigation.
- Shows episode context or a warning in Appointment Workspace.
- Adds AI Assisted Clinical Plan proposal/review/confirm flow.
- Stores only physician-confirmed plans as active.
- Enforces one active confirmed clinical plan per episode in PostgreSQL.
- Stores the physician conclusion used for the plan.
- Shows clinical decision timeline.
- Readiness does not block or warn on appointments without an episode.
- Writes audit for create, update, close, link and unlink actions.
- Seeds demo episodes.

## What It Deliberately Does Not Do

- Does not allow real patient data.
- Does not implement Workflow Engine.
- Does not implement Knowledge Engine.
- Does not implement AI automation or autonomous medical decisions.
- Does not integrate a real AI provider yet.
- Does not implement new clinical modules.
- Does not implement documents, labs, prescriptions or diagnosis coding.
- Does not implement real Croatian fiscalization.
- Does not block old appointments without an episode.
- Does not make appointments require episodes.
- Does not define the primary clinical workflow.

## API Overview

- `GET /api/episodes`
- `POST /api/episodes`
- `GET /api/episodes/{id}`
- `PATCH /api/episodes/{id}`
- `POST /api/episodes/{id}/close`
- `GET /api/patients/{patient_id}/episodes`
- `GET /api/episodes/{id}/appointments`
- `POST /api/episodes/{id}/clinical-plans/generate`
- `GET /api/episodes/{id}/clinical-plans`
- `GET /api/episodes/{id}/clinical-plans/active`
- `PATCH /api/clinical-plans/{id}`
- `POST /api/clinical-plans/{id}/confirm`
- `POST /api/clinical-plans/{id}/reject`
- `GET /api/episodes/{id}/clinical-timeline`

Appointment create/update accepts optional `episode_id`.

## UI Overview

- `/episodes` lists clinical episodes.
- `/episodes/new` creates a demo/pilot episode for an existing patient.
- `/episodes/:id` opens Episode Workspace.
- Patient Workspace prioritizes Clinical Knowledge and source-linked documents. Episode views are deferred.
- Appointment form can select an active/open episode after patient selection.
- Appointment detail shows the episode link or a non-blocking warning.
- Episode Workspace shows active confirmed plan, pending AI suggestion and decision timeline.

## Relationship To Future Workflow Engine

Episode is the clinical story. Workflow Engine will later attach operational tasks and steps to that story.

This MVP does not create tasks or automate clinical operations.

## Relationship To Future Knowledge Engine

Knowledge Engine will later bring structured domain reasoning and guidelines.

This MVP stores context only. It does not calculate guidelines, diagnoses or medical recommendations.

## Relationship To Future AI Layer

AI can prepare a structured suggestion. It must remain visibly assistant-like and clinician-controlled.

This MVP adds no autonomous AI automation. Physician confirmation is required before an episode changes.
