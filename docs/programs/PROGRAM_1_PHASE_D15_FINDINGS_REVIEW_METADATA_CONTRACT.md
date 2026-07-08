# Program 1 Phase D15 - Findings Review Metadata Contract

Status: review metadata contract

## Proposed Metadata

- `reviewed_by_user_id`
- `reviewed_at`
- `review_note`
- review limitations
- source context snapshot/reference
- lifecycle status at review time

## Physician Responsibility

Physician review is required for clinical interpretation and decision-making.

Review metadata must not imply diagnosis, treatment plan, clearance, override or patient instruction by itself.

## Role Limits

- nurse review may support preparation only if later policy permits
- reception review is administrative only
- AI/API keys cannot be final reviewers
- system jobs cannot create official review

## Source Context

Review metadata must be tied to source context.

Review without source context is unsafe and should not become official finding review.

## Not Implemented

D15 does not implement review workflow, endpoint, service, audit event or UI.

