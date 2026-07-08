# Program 1 Phase D93 - Open Question ORM Shape Deferral

Status: deferred

## Decision

Do not add a `ClinicalOpenQuestion` ORM model or Alembic migration in D88-D98.

## Why The ORM Model Is Deferred

- source-linking rules need one more review before becoming DB constraints
- review metadata is not yet a runtime workflow
- audit and retention expectations are not finalized
- future relationship to findings, source documents and extraction candidates needs migration review
- adding an ORM model too early could imply persistence readiness

## Why The Migration Is Deferred

- no runtime endpoint or service exists
- no automatic question creation is approved
- rollback and backup/restore implications need a dedicated migration gate
- production and real-data use remain no-go

## Prerequisites Before Model Or Migration

- approved migration review gate
- confirmed source-linking constraints
- safe lifecycle status constraints
- review metadata boundary
- audit/retention policy
- no-go route/service/UI tests remain green

## Explicit Non-Goals

- no endpoint
- no service
- no UI
- no automatic question creation
- no Task, Outcome Evidence or patient messaging
- no diagnosis, treatment, approval, clearance or override

## Future Candidate Phase

`Program 1 Phase D99` or later may consider a migration draft if guardrails remain clean.
