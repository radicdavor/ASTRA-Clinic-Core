# Episode Engine MVP

Status: Foundation implemented for demo/pilot use only.

Episode Engine adds Clinical Episode as the first clinical story object in ASTRA Clinic Core.

## What It Does Now

- Adds `ClinicalEpisode` as a backend model.
- Links episodes to patients.
- Allows appointments to optionally link to an episode.
- Prevents linking an appointment to an episode from another patient.
- Adds episode list, create page and Episode Workspace.
- Shows episodes in Patient Workspace.
- Shows episode context or a warning in Appointment Workspace.
- Adds readiness awareness for appointments without an episode.
- Writes audit for create, update, close, link and unlink actions.
- Seeds demo episodes.

## What It Deliberately Does Not Do

- Does not allow real patient data.
- Does not implement Workflow Engine.
- Does not implement Knowledge Engine.
- Does not implement AI automation.
- Does not implement new clinical modules.
- Does not implement documents, labs, prescriptions or diagnosis coding.
- Does not implement real Croatian fiscalization.
- Does not block old appointments without an episode.

## API Overview

- `GET /api/episodes`
- `POST /api/episodes`
- `GET /api/episodes/{id}`
- `PATCH /api/episodes/{id}`
- `POST /api/episodes/{id}/close`
- `GET /api/patients/{patient_id}/episodes`
- `GET /api/episodes/{id}/appointments`

Appointment create/update accepts optional `episode_id`.

## UI Overview

- `/episodes` lists clinical episodes.
- `/episodes/new` creates a demo/pilot episode for an existing patient.
- `/episodes/:id` opens Episode Workspace.
- Patient Workspace has an `Epizode` tab and active episode count.
- Appointment form can select an active/open episode after patient selection.
- Appointment detail shows the episode link or a non-blocking warning.

## Relationship To Future Workflow Engine

Episode is the clinical story. Workflow Engine will later attach operational tasks and steps to that story.

This MVP does not create tasks or automate clinical operations.

## Relationship To Future Knowledge Engine

Knowledge Engine will later bring structured domain reasoning and guidelines.

This MVP stores context only. It does not calculate guidelines, diagnoses or medical recommendations.

## Relationship To Future AI Layer

AI may later help summarize, organize and suggest. It must remain visibly assistant-like and clinician-controlled.

This MVP adds no AI automation.
