# Program 1 Synthetic Sandbox Implementation Track Phase A - Local Synthetic Patient Workflow Prototype

Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use.

## Status

Program 1 Synthetic Sandbox Implementation Track Phase A creates a local-only synthetic workflow prototype. It is implementation-oriented only inside an isolated sandbox path and does not authorize production use, real patient data, PHI/PII processing, EHR/EMR connection, external integrations, patient messaging, appointment mutation, autonomous diagnosis, autonomous treatment, clinical writeback, approval/clearance/override capability, or go-live.

## Scope

Phase A adds:

- a synthetic patient model
- a synthetic encounter model
- a synthetic finding model
- a synthetic clinician review placeholder model
- sample synthetic fixtures
- a local workflow summary helper
- targeted synthetic-only tests
- sandbox documentation

## Non-Scope

Phase A does not add runtime backend or frontend wiring, database persistence, network calls, external API calls, clinical data imports, environment secrets, deployment configuration, production behavior, clinical decision execution, patient communication, appointment mutation, clinical writeback, approval/clearance/override capability, or go-live authorization.

## Files

- `sandbox/program1/models.py`
- `sandbox/program1/sample_data.py`
- `sandbox/program1/workflow.py`
- `sandbox/program1/README.md`
- `tests/sandbox/program1/test_synthetic_workflow.py`

## Safety Checks

The sandbox rejects obvious real-identifier-like values in synthetic fields, requires synthetic/demo/example prefixes, and exposes workflow summary flags showing that clinical use, real patient data, PHI/PII, external integrations, appointment mutation, patient messaging, and approval/override capability are not enabled.

## Current Decision

Program 1 remains non-production and not for clinical use. The sandbox is local-only and synthetic-only. No Phase B, Implementation Proposal Track, production deployment, real-data use, PHI/PII processing, or go-live work is opened by Phase A.
