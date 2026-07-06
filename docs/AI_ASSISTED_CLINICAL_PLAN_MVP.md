# AI Assisted Clinical Plan MVP

Status: Episode Engine extension for demo/pilot use only.

## Purpose

AI Assisted Clinical Plan lets ASTRA prepare a structured proposal after a visit, consultation or procedure.

The AI suggestion is not official. The physician reviews, edits and confirms. Only confirmed plans update the Clinical Episode.

## Domain Object

`ClinicalPlan` belongs to `ClinicalEpisode`.

Current fields include:

- `episode_id`
- `source`
- `status`
- `proposed_episode_status`
- `next_action`
- `due_date`
- `priority`
- `rationale`
- `suggested_follow_up`
- `physician_conclusion`
- `ai_confidence`
- `physician_confirmed`
- `confirmed_by`
- `confirmed_at`

## Current Workflow

1. Physician enters procedure context, findings and conclusion.
2. ASTRA generates an AI-labeled structured proposal.
3. Physician may edit, reject or confirm.
4. Only confirmation makes the plan active.
5. Confirmation updates the episode status/priority from the plan.
6. Audit and clinical timeline record the decision.

Only one confirmed active plan may exist per episode. Older active plans are archived before a new confirmed plan becomes active.

When a new AI suggestion is generated, older unconfirmed draft/waiting suggestions for the same episode are marked cancelled/superseded.

## API

- `POST /api/episodes/{episode_id}/clinical-plans/generate`
- `GET /api/episodes/{episode_id}/clinical-plans`
- `GET /api/episodes/{episode_id}/clinical-plans/active`
- `PATCH /api/clinical-plans/{plan_id}`
- `POST /api/clinical-plans/{plan_id}/confirm`
- `POST /api/clinical-plans/{plan_id}/reject`
- `GET /api/episodes/{episode_id}/clinical-timeline`

## UI

Episode Workspace shows:

- active confirmed clinical plan
- pending AI suggestion
- physician conclusion attached to the plan
- confirm/edit/reject actions
- clinical decision timeline
- appointment context
- findings/pathology note explaining that documents are not implemented yet

## Safety Rules

AI must not:

- create the official plan
- mark plans confirmed
- close episodes automatically
- prescribe medication
- create appointments
- hide uncertainty
- invent diagnoses

Low-confidence suggestions display manual review language.

Allowed values are intentionally whitelisted for episode status, plan priority and plan next action so the shared ASTRA language remains stable.

## Deliberately Deferred

- real AI provider integration
- Workflow Engine
- Knowledge Engine
- documents
- labs/pathology documents
- prescriptions
- automatic surveillance rules
- production clinical use
