# Program 1 Synthetic Read-Only UI Track Phase B - Synthetic Data Contract and Fixture Layer

Status: complete.

Phase B creates the frontend-only fixture contract for the synthetic review workspace.

Fixture source:

- The UI fixtures are repository-controlled TypeScript data in `frontend/src/program1/data/syntheticScenarios.ts`.
- They are conceptually derived from the existing terminal sandbox scenarios in `sandbox/program1`.
- They are not parsed from Python at runtime and are not loaded from a backend endpoint.

Data types:

- `SyntheticScenario`
- `SyntheticTimelineEvent`
- `SyntheticEvidenceItem`
- `SyntheticFinding`
- `SyntheticReadinessItem`
- `SyntheticProvenance`

Validation:

- `validateSyntheticScenarios` runs when fixtures are imported.
- It validates unique scenario IDs, nested IDs, synthetic-only markers, no real-data provenance, required text fields, evidence references, limitations, and prohibited interpretations.
- Validation is passive and local. It sends nothing anywhere.

Scenario inventory:

- `SYN-ALPHA`
- `SYN-BETA`
- `SYN-GAMMA`
- `SYN-DELTA`
- `SYN-EPSILON`

No-real-data rules:

- no real names
- no dates of birth
- no phone numbers
- no emails
- no Croatian OIB-like values
- no medical record numbers
- no real addresses
- no copied clinical reports

Limitations:

- Fixtures are synthetic demo material only.
- They are not de-identified patient data.
- They are not clinical validation evidence.
- They do not authorize production use, PHI/PII processing, clinical use, backend integration, persistence, export, or go-live.
