# Program 1 Phase C7 - Advisory Signal Preview Mapping

Status: design-only preview mapping

## Purpose

This document defines how existing Clinical Readiness Preview items may map into future advisory signals.

No runtime mapper is implemented in C7.

## Preview Item To Advisory Signal

Mapping proposal:

- preview item key -> advisory `signal_key`
- preview item label -> advisory `label`
- preview item category -> advisory `category`
- preview item severity -> advisory `severity`
- preview item source type/ref/label -> advisory `source_type` and `source_reference`
- preview item suggested action -> advisory `explanation`
- preview limitations -> advisory `limitations`
- snapshot id if available -> future optional relation

## Severity Mapping

Preview severity should be converted carefully:

- `info` -> `info`
- `warning` -> `warning`
- `blocking` -> `review_required`
- `critical` -> `review_required`

The mapped signal still must not block workflow.

## Missing Input Handling

Missing input should become:

- severity: `missing_input`
- category: `documentation` or `logistics`
- explanation: human-readable missing input

## Stale Snapshot Handling

Stale snapshots should produce a review-needed advisory signal only if displayed in a future read-only context.

Stale snapshot signal is not clearance and not blocking.

## No Decision Semantics

Mapped advisory signals must keep:

- `is_decision = false`
- no approval status
- no clearance status
- no override status
- no enforcement result

## Recommended Next Task

`Program 1 Phase C8 - Advisory Signal Regression Guard`
