# Program 1 Phase D - UI and Accessibility Contract

## Structure

- one H1 identifying the moderator runner
- persistent evaluation boundary region
- three-item transient summary: preflight, reviewed tasks, stop state
- preflight section with native checkboxes
- ordered task list numbered 1 through 8
- native radio groups for transient task state
- collapsible success signals using `details` and `summary`
- explicit stop alert
- stop and reset controls

## Accessibility

- native checkbox and radio semantics
- fieldset and legend grouping for each task
- labeled progress and state regions
- `role=status` for transient task and preflight summaries
- `role=alert` for stop state
- visible global focus treatment
- reduced-motion protection inherited from Phase B
- single-column mobile layout below 980 px
- no page-level horizontal overflow at 390 px

## Design Decision

The runner uses the existing ASTRA palette, typography, spacing, and eight-pixel radii. Sequential number markers are used only because the Phase C protocol has a mandatory order. Safety red is reserved for the persistent boundary and stopped state; teal remains informational navigation emphasis.

