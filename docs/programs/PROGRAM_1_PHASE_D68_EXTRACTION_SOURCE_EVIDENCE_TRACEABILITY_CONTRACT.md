# Program 1 Phase D68 - Extraction Source Evidence Traceability Contract

Status: traceability contract

## Purpose

Define minimum source evidence needed before any extraction candidate could become a persisted finding in a later phase.

## Required Traceability

Candidate findings must preserve:

- source document id or external source reference
- source document type
- source label/title
- source text span or excerpt reference if available
- page, section or field path if available
- source date if known
- source author or institution if known
- extraction method
- extraction timestamp
- source limitations

## Before Persistence

Before a candidate may be persisted later, reviewers must be able to inspect source context and understand what source element produced the candidate.

## Missing Source Data

Missing source details must be represented as limitations. Missing source data must not be filled with invented values.

## Official Truth Boundary

Traceability enables review. It does not make extracted content official clinical truth.

No official interpretation exists without human review under future policy.

