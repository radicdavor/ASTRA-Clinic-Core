# Program 1 Synthetic Read-Only UI Evaluation Track Phase C

## External Clinician Evaluation Kit - Scope and Boundaries

Status: kit complete; external session not executed.

## Purpose

Phase C prepares a complete, repeatable kit for a future moderated evaluation with a clinician using only the local Program 1 synthetic read-only workspace.

The kit is preparation, not evidence that a clinician session occurred. No participant response, score, quote, observation, or decision may be recorded as completed until a real authorized participant performs the session.

## Architecture Check

- human above software: the evaluator observes comprehension rather than prescribing behavior
- one source of truth: repository-controlled synthetic scenarios remain the only evaluation content
- one shared language: Program 1 labels and safety language remain unchanged
- modular Clinic Core: documentation-only evaluation kit; no domain or API change
- AI as assistant: AI may organize notes but may not invent participant feedback
- audit and safety: session identity, consent, deviations, stop events, and disposition are explicitly recorded

Change category: information/documentation workflow.

## Authorized Future Session Boundary

- one named adult clinician participant per session
- one named moderator
- one named observer/reviewer when available
- local machine only
- repository-controlled synthetic scenarios only
- read-only interaction only
- no patient, appointment, institutional, or practice-derived information
- no recording unless separately and explicitly consented
- no production, clinical care, or patient-facing use

## Prohibited

- real patient examples, screenshots, notes, exports, or identifiers
- asking the participant to enter clinical free text
- interpreting output as diagnosis, treatment, triage, recommendation, clearance, or priority
- changing application data or using write-capable Clinic Core screens as evaluation tasks
- hidden observation, coercion, performance appraisal, or competency grading
- fabricated answers, inferred consent, or retroactive consent
- clinical validation, certification, production, or go-live claims

## Phase C Kit Contents

- participant eligibility and consent record
- moderator runbook
- synthetic task script
- observation and scoring form
- stop-condition and deviation protocol
- evidence and decision packet
- final readiness matrix and closure report

