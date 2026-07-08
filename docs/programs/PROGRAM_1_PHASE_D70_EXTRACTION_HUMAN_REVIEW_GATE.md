# Program 1 Phase D70 - Extraction Human Review Gate

Status: human review gate

## Purpose

Define the human review gate for future extraction candidates.

## Who May Review

Future policy should separate:

- physician review for clinical interpretation
- authorized clinical staff review for source-quality support where explicitly allowed
- nurse preparation support without final clinical decision authority unless later policy narrows it
- reception limited to administrative/source availability context

AI agents, API keys and system jobs may not be final reviewers.

## Review Before Persistence

Candidate findings require human review before any future persistence path may treat them as stored findings.

## Review Before Interpretation

Human review is required before clinical interpretation, patient communication, treatment planning or follow-up recommendations.

## Review Does Not Create Workflow Objects

Review must not automatically create:

- Task
- Outcome Evidence
- patient message
- appointment status mutation
- diagnosis
- treatment plan
- approval, clearance or override

## Future Audit Requirements

Future review audit should capture actor, role, timestamp, source reference, candidate key, limitations and reason/note.

Audit evidence must remain access/review evidence, not Outcome Evidence.

