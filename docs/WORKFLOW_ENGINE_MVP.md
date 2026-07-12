# ASTRA Workflow Engine MVP

Status: implemented.

## Purpose

Workflow Engine answers three operational questions:

- what needs to happen next
- who is responsible
- what must be completed before the work can close

A workflow task is an operational object. It is not a diagnosis, treatment recommendation, clinical priority decision, clearance, or replacement for physician judgment.

## Domain model

`WorkflowTask` belongs to one patient and may reference an episode, appointment, assignee provider, responsible role, and template. It has an explicit status, operational priority, due date, description, and ordered checklist.

Statuses:

- `open`
- `in_progress`
- `waiting`
- `completed`
- `cancelled`

Priorities:

- `routine`
- `important`
- `urgent`

Priority describes operational handling only. It does not represent clinical triage.

## Safety boundaries

- A task cannot reference an episode or appointment belonging to another patient.
- A task with unfinished checklist items cannot be completed.
- Clinical findings, open questions, AI suggestions, or reviewed documents do not automatically create tasks.
- Creating, updating, completing, and changing checklist items is audited.
- No real-data authorization, autonomous AI workflow, external integration, or production approval is introduced.

## API

- `GET/POST /api/workflow-templates`
- `GET/POST /api/workflow-tasks`
- `GET/PATCH /api/workflow-tasks/{id}`
- `POST /api/workflow-tasks/{id}/checklist/{item_id}/toggle`
- `GET /api/patients/{id}/workflow-tasks`
- `GET /api/episodes/{id}/workflow-tasks`

Permissions:

- `workflow_tasks.read`
- `workflow_tasks.write`
- `workflow_templates.manage`

## User interface

- `/workflow` provides a status-based work strip and task creation.
- `/workflow/{id}` provides ownership, status, due date, checklist, and audit context.
- Patient Workspace and Episode Workspace show active next-step tasks.

The UI uses existing ASTRA action language and safety patterns. Completing a task is confirmed and audited.

## Seed templates

- result review
- appointment preparation
- follow-up organization

Templates provide checklists, not clinical decisions.

## Validation

Backend coverage verifies template application, checklist completion gates, audit events, cross-patient link rejection, permissions, and patient/episode task views. Frontend build and pilot smoke protect routes and safety wording.

## Deferred

- workflow automation triggered by clinical findings
- AI-created or AI-assigned tasks
- notifications and external messaging
- recurring tasks
- multi-stage branching workflow definitions
- specialty-specific workflows
- production and real-data enablement
