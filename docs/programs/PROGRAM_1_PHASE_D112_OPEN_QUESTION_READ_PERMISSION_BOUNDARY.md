# Program 1 Phase D112 - Open Question Read Permission Boundary

Status: documented

## Future Permission Proposal

Proposed read permission name: `clinical_open_questions.read`.

This permission is not seeded in this phase.

## Demo/Pilot Read Expectations

- physician and admin roles may be candidates for future read access
- nurse read access requires separate review because open questions need clinical interpretation
- reception access should remain no-go unless a specific non-clinical need is approved

## API Key, AI Agent And System Boundaries

API keys, AI agents and system jobs should be denied by default unless a later phase explicitly approves a narrow read-only scope. Read access must not allow AI/system actors to review, resolve, create or interpret questions as clinical truth.

## Permission Does Not Mean Review

Read permission does not imply:

- review permission
- write permission
- diagnosis or treatment authority
- approval, clearance or override authority
- Task creation
- Outcome Evidence creation
- patient messaging

## Current Phase Boundary

No read permission seed is added in this phase.
