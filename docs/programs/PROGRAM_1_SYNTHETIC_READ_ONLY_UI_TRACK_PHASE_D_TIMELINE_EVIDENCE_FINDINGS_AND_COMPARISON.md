# Program 1 Synthetic Read-Only UI Track Phase D - Timeline, Evidence, Findings, and Comparison

Status: complete.

Timeline:

- uses relative labels such as `Dan 0`, `Pregled 1`, and `Lokalni demo`
- links visually to synthetic evidence IDs
- remains descriptive
- does not claim causality, urgency, clinical priority, or next clinical action

Evidence:

- shows type, title, synthetic source label, availability state, and summary
- states are limited to `available`, `missing`, and `ambiguous`
- no upload, preview of real reports, download, export, or file action exists

Findings:

- remain descriptive and synthetic
- states are limited to `open`, `resolved-in-scenario`, and `uncertain`
- each finding shows linked evidence and limitation
- no severity score, risk score, assignment, acknowledgment, approval, or completion control exists

Readiness/completeness:

- describes scenario documentation completeness only
- explicitly states it is not clinical readiness of a patient

Comparison:

- supports exactly two selected scenarios
- prevents same-scenario comparison by showing a safe empty state
- compares identity, review question, evidence availability, finding states, completeness descriptors, limitations, and prohibited interpretations
- has no score, winner, ranking, urgency, priority, recommendation, diagnosis, treatment advice, or triage behavior

Determinism:

- scenario order is stable: Alpha, Beta, Gamma, Delta, Epsilon
- all content is bundled in repository-controlled fixtures
