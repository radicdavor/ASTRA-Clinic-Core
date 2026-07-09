# Program 1 Synthetic Sandbox Implementation Track Phase B - Local Sandbox Usability Loop

Synthetic-only. Non-production. No real patient data. No PHI/PII. Not for clinical use.

## Status

Program 1 Synthetic Sandbox Implementation Track Phase B improves local sandbox usability with a local-only command runner, clearer workflow summary output, an additional synthetic scenario, README run instructions, and unittest coverage.

## Scope

Phase B adds:

- local-only CLI entry point: `python -m sandbox.program1.cli`
- scenario registry with `alpha` and `beta` synthetic scenarios
- console rendering with safety banner and disabled capability flags
- JSON output option for local inspection
- targeted unittest coverage for scenarios and CLI behavior
- conservative documentation updates

## Non-Scope

Phase B does not add cloud deployment, Google Cloud config, Docker, Kubernetes, Terraform, CI/CD, network calls, database connections, external APIs, real patient data, PHI/PII, EHR/EMR access, patient messaging, appointment mutation, clinical writeback, approval/clearance/override capability, production-readiness claim, or go-live authorization.

## Current Decision

Program 1 remains synthetic-only, local-only, non-production, and not for clinical use. Phase B does not start Phase C, an Implementation Proposal Track, production deployment, real-data work, PHI/PII work, integration work, or go-live work.
