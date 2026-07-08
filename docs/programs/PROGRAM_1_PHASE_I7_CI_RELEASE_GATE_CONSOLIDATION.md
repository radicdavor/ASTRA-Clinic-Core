# Program 1 Phase I7 - CI Release Gate Consolidation

## Required Gate

- `git diff --check`
- `python -m py_compile` for core backend modules
- `alembic upgrade head`
- snapshot tests
- acknowledgment tests
- findings tests
- open question tests
- review tests
- timeline tests
- full backend suite
- frontend typecheck
- frontend build
- frontend smoke

## Safety Checks

- no forbidden write routes
- no forbidden UI action labels
- no forbidden clinical decision wording
- no missing README/roadmap links for completed governance docs

## Release Blockers

- failing tests
- new write workflow without approval
- production/real-data claim
- missing source-linking limitation
- permission seed without governance review
- UI action that implies review, approval, clearance, diagnosis, treatment, Task, Outcome Evidence or patient messaging

