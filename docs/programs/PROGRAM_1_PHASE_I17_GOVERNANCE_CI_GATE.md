# Program 1 Phase I17 - Governance CI Gate

## Required Checks

- all targeted backend suites for timeline, review, open questions, extraction, findings, readiness and acknowledgments
- full backend suite
- frontend typecheck
- frontend build
- frontend smoke
- Alembic upgrade head
- no forbidden route checks
- no forbidden wording checks
- README and roadmap links for completed governance docs

## Release Blocker Criteria

- failing migration or test
- new endpoint/service/UI/permission seed in a governance-only phase
- production or real-data claim
- missing no-go documentation for a newly introduced surface
- forbidden wording that implies approval, clearance, diagnosis, treatment, Task, Outcome Evidence or patient messaging

