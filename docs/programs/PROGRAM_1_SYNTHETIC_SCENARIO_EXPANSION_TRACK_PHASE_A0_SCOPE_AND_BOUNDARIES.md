# Program 1 Synthetic Scenario Expansion Track Phase A0 - Scope and Boundaries

Status: local-only synthetic scenario expansion. Terminal-only. Non-production. Not for clinical use.

Allowed:

- add gamma, delta, and epsilon to the existing local scenario registry
- update existing local terminal commands so new scenarios work through the existing `--scenario` argument
- update compare-scenarios to include the expanded scenario set
- add tests for new synthetic scenarios
- update documentation, README, sandbox README, and roadmap

Prohibited:

- web UI or browser UI
- server or API endpoint
- network or database access
- external integrations
- file persistence or export files
- EHR/EMR access
- real-data ingestion or PHI/PII handling
- patient messaging or appointment mutation
- workflow enforcement
- Task engine or Outcome Evidence behavior
- clinical write workflows or clinical writeback
- autonomous diagnosis or treatment
- triage execution or patient instruction delivery
- clinician-facing executable recommendations
- approval/clearance/override capability
- production-readiness or go-live authorization
- cloud deployment or deployment automation

Current decision: add only local synthetic scenarios and preserve No-UI Hold.
