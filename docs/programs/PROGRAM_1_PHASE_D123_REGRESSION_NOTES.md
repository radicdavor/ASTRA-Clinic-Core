# Program 1 Phase D123 Regression Notes

Status: read permission seed added

## Completed

- Added `clinical_open_questions.read` as a read-only permission.
- Added the permission to admin through the global permission set and to physician role explicitly.
- Left nurse, receptionist, API key, AI agent and system job write/review permissions absent.

## Not Added

- No `clinical_open_questions.write`.
- No review, approve, clear or resolve permission.
- No endpoint or frontend UI was added in D123.

## Safety Boundary

Read permission allows future source-linked display only. It does not imply review, diagnosis, treatment, approval, clearance, override, Task, Outcome Evidence, patient messaging or production readiness.
