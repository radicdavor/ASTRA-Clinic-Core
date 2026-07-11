# Program 1 Phase E - Candidate Identity Contract

## Candidate

Name: `Program 1 Local Synthetic Evaluation Session Candidate`.

Required identity:

- exact 40-character Git commit SHA
- clean working tree
- Program 1 review route
- Program 1 evaluation runner route
- repository-controlled scenario fixture
- repository-controlled task fixture
- Phase C eligibility, consent, moderation, task, observation, stop, and evidence documents
- Phase D closure record

Branch names, `main`, `latest`, mutable tags, short SHAs, dirty trees, or approximate dates are not sufficient candidate identities.

## Material Change Rule

Any change to the following invalidates the prior gate result:

- commit SHA
- runner or review UI
- scenario or task fixtures
- route or navigation
- safety copy
- preflight or stop logic
- Phase C controlled templates
- forbidden-primitive list
- gate implementation

After any material change, rerun the gate on a new clean commit.

