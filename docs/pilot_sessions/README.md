# Pilot Sessions

Use this folder to record each closed pilot session. Do not include real patient data, real identifiers, screenshots with personal data, or production credentials.

## How to Record a Session

1. Start from `docs/PILOT_RUNBOOK.md`.
2. Record the environment, commit SHA, participant roles, and date/time.
3. Mark each runbook step as completed or failed.
4. Capture issues with enough context to reproduce them using demo data.
5. Convert actionable findings into GitHub issues using `.github/ISSUE_TEMPLATE/pilot_feedback.yml`.
6. Link issue numbers back to the session notes.

## Feedback Template

Use `docs/PILOT_FEEDBACK_TEMPLATE.md` during facilitated interviews, then convert confirmed findings into GitHub issues.

## Severity Definitions

- P0: data corruption/security issue/demo cannot proceed.
- P1: core workflow blocked.
- P2: confusing but workaround exists.
- P3: cosmetic or minor wording issue.

## Triage Rules

- P0/P1 must be resolved before a v0.1 pilot release tag.
- P2 findings should be grouped by workflow and planned before expanding module scope.
- P3 findings can be batched into wording and polish passes.
- Any real-data concern must also receive the `real-data-blocker` label.
