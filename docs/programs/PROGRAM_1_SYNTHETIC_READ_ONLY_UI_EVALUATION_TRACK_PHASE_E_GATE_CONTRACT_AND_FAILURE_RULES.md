# Program 1 Phase E - Gate Contract and Failure Rules

## Required Checks

- all required Phase C/D files exist
- review and evaluation routes exist
- evaluation navigation label exists
- exactly six preflight definitions exist
- exactly eight ordered tasks exist
- keyboard-only task exists
- real-data prohibition remains present
- runner files contain no network, storage, cookie, clipboard, print, file-export, streaming, beacon, download, or unsafe HTML primitives
- exact full commit SHA is available
- working tree is clean

## Failure Behavior

Any failed check produces:

- readiness `NOT READY`
- non-zero process exit
- exact failed-check identifiers

No majority threshold, warning-only bypass, or manual assumption converts a failure into readiness.

## Dirty-Tree Rule

A dirty tree always fails, even when every content check passes. The future session candidate must be reproducible from a fixed commit.

## Non-Claims

Gate success is not evidence of participant eligibility, consent, session execution, usability success, clinical validation, accessibility certification, security certification, production readiness, or go-live readiness.

